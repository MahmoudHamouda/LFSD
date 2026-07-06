"""
Database-backed governance stores — portable (SQLAlchemy Core, own tables).

These make consent, decision logging, and idempotency *operational with a real
database* without coupling to any host application's models. Point them at any
SQLAlchemy ``Engine`` (SQLite, Postgres, …); ``create_all(engine)`` provisions
the tables under an ``rai_`` prefix.

Security properties:
  * **Append-only.** No update/delete is exposed. History is the source of truth.
  * **Tamper-evident.** Every row is hash-chained (``record_hash`` over the row's
    canonical content + the previous row's hash), so any silent edit/deletion
    breaks the chain — verifiable via ``verify_chain()``.
  * **Parameterized.** All access is through SQLAlchemy Core; no string SQL.
  * **No PII by contract.** Stores hold pseudonymous ids, purposes, decisions,
    and reasons — never raw identifiers. Callers must keep PII out (see pii.py).
"""

from __future__ import annotations

import hashlib
import json
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    insert,
    select,
)
from sqlalchemy.engine import Engine

from .consent import ConsentRecord

RAI_METADATA = MetaData()

# Genesis hash for the first link in each chain.
_GENESIS = "0" * 64


def _canonical(payload: dict) -> str:
    """Deterministic serialization for hashing (stable key order)."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _hash(payload: dict, prev_hash: str) -> str:
    return hashlib.sha256((_canonical(payload) + prev_hash).encode("utf-8")).hexdigest()


consent_records = Table(
    "rai_consent_records",
    RAI_METADATA,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", String(255), nullable=False, index=True),
    Column("purpose", String(255), nullable=False, index=True),
    Column("granted", Boolean, nullable=False),
    Column("policy_version", String(64), nullable=False),
    Column("timestamp", String(40), nullable=False),  # ISO 8601, caller-supplied
    Column("source", String(64), nullable=False, default="app"),
    Column("metadata_json", Text, nullable=True),
    Column("prev_hash", String(64), nullable=False),
    Column("record_hash", String(64), nullable=False),
)

decision_log = Table(
    "rai_decision_log",
    RAI_METADATA,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("timestamp", String(40), nullable=False),
    Column("subject_id", String(255), nullable=False, index=True),
    Column("action", String(128), nullable=False),
    Column("decision", String(32), nullable=False),
    Column("risk_class", String(32), nullable=True),
    Column("reason", Text, nullable=False),
    Column("correlation_id", String(64), nullable=True, index=True),
    Column("metadata_json", Text, nullable=True),
    Column("prev_hash", String(64), nullable=False),
    Column("record_hash", String(64), nullable=False),
)

idempotency_keys = Table(
    "rai_idempotency_keys",
    RAI_METADATA,
    Column("key", String(128), primary_key=True),
    Column("created_at", String(40), nullable=False),
)


def create_all(engine: Engine) -> None:
    """Create the governance tables if they do not already exist."""
    RAI_METADATA.create_all(engine)


# ---------------------------------------------------------------------------
# Consent
# ---------------------------------------------------------------------------


class SqlConsentStore:
    """Append-only, hash-chained ``ConsentStore`` backed by SQLAlchemy."""

    def __init__(self, engine: Engine):
        self.engine = engine

    def append(self, record: ConsentRecord) -> None:
        payload = {
            "user_id": record.user_id,
            "purpose": record.purpose,
            "granted": record.granted,
            "policy_version": record.policy_version,
            "timestamp": record.timestamp,
            "source": record.source,
            "metadata_json": _canonical(record.metadata) if record.metadata else None,
        }
        with self.engine.begin() as conn:
            prev = conn.execute(
                select(consent_records.c.record_hash)
                .order_by(consent_records.c.id.desc())
                .limit(1)
            ).scalar()
            prev_hash = prev or _GENESIS
            conn.execute(
                insert(consent_records).values(
                    **payload,
                    prev_hash=prev_hash,
                    record_hash=_hash(payload, prev_hash),
                )
            )

    def history(self, user_id: str, purpose: str) -> List[ConsentRecord]:
        with self.engine.connect() as conn:
            rows = conn.execute(
                select(consent_records)
                .where(consent_records.c.user_id == user_id)
                .where(consent_records.c.purpose == purpose)
                .order_by(consent_records.c.id.asc())
            ).all()
        out: List[ConsentRecord] = []
        for r in rows:
            out.append(
                ConsentRecord(
                    user_id=r.user_id,
                    purpose=r.purpose,
                    granted=r.granted,
                    policy_version=r.policy_version,
                    timestamp=r.timestamp,
                    source=r.source,
                    metadata=json.loads(r.metadata_json) if r.metadata_json else {},
                )
            )
        return out

    def verify_chain(self) -> bool:
        """Recompute the hash chain; False if any row was tampered/deleted."""
        with self.engine.connect() as conn:
            rows = conn.execute(
                select(consent_records).order_by(consent_records.c.id.asc())
            ).all()
        prev_hash = _GENESIS
        for r in rows:
            payload = {
                "user_id": r.user_id,
                "purpose": r.purpose,
                "granted": r.granted,
                "policy_version": r.policy_version,
                "timestamp": r.timestamp,
                "source": r.source,
                "metadata_json": r.metadata_json,
            }
            if r.prev_hash != prev_hash or r.record_hash != _hash(payload, prev_hash):
                return False
            prev_hash = r.record_hash
        return True


# ---------------------------------------------------------------------------
# Decision log
# ---------------------------------------------------------------------------


class SqlDecisionLog:
    """Append-only, hash-chained audit log of policy/assessment decisions."""

    def __init__(self, engine: Engine):
        self.engine = engine

    def append(
        self,
        *,
        timestamp: str,
        subject_id: str,
        action: str,
        decision: str,
        reason: str,
        risk_class: Optional[str] = None,
        correlation_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> None:
        payload = {
            "timestamp": timestamp,
            "subject_id": subject_id,
            "action": action,
            "decision": decision,
            "risk_class": risk_class,
            "reason": reason,
            "correlation_id": correlation_id,
            "metadata_json": _canonical(metadata) if metadata else None,
        }
        with self.engine.begin() as conn:
            prev = conn.execute(
                select(decision_log.c.record_hash)
                .order_by(decision_log.c.id.desc())
                .limit(1)
            ).scalar()
            prev_hash = prev or _GENESIS
            conn.execute(
                insert(decision_log).values(
                    **payload,
                    prev_hash=prev_hash,
                    record_hash=_hash(payload, prev_hash),
                )
            )

    def recent(self, subject_id: Optional[str] = None, limit: int = 100) -> List[dict]:
        stmt = select(decision_log).order_by(decision_log.c.id.desc()).limit(limit)
        if subject_id is not None:
            stmt = stmt.where(decision_log.c.subject_id == subject_id)
        with self.engine.connect() as conn:
            rows = conn.execute(stmt).all()
        return [dict(r._mapping) for r in rows]

    def verify_chain(self) -> bool:
        with self.engine.connect() as conn:
            rows = conn.execute(
                select(decision_log).order_by(decision_log.c.id.asc())
            ).all()
        prev_hash = _GENESIS
        for r in rows:
            payload = {
                "timestamp": r.timestamp,
                "subject_id": r.subject_id,
                "action": r.action,
                "decision": r.decision,
                "risk_class": r.risk_class,
                "reason": r.reason,
                "correlation_id": r.correlation_id,
                "metadata_json": r.metadata_json,
            }
            if r.prev_hash != prev_hash or r.record_hash != _hash(payload, prev_hash):
                return False
            prev_hash = r.record_hash
        return True


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


class SqlIdempotencyStore:
    """First-writer-wins idempotency keys — blocks duplicate action execution."""

    def __init__(self, engine: Engine):
        self.engine = engine

    def register(self, key: str, timestamp: str) -> bool:
        """
        Returns True if ``key`` is new (caller may proceed), False if it already
        exists (duplicate — caller must not re-execute). Atomic via PK conflict.
        """
        try:
            with self.engine.begin() as conn:
                conn.execute(
                    insert(idempotency_keys).values(key=key, created_at=timestamp)
                )
            return True
        except Exception:
            return False
