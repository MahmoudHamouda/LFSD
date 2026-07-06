"""
Consent capture — persisted, versioned, auditable.

Bridge #2, part 2. The gap analysis found consent was a default-True parameter
with no backing store. Here consent is a first-class, versioned record with an
explicit purpose and lifecycle (granted / withdrawn / expired), plus a storage
interface an FI backs with their own database.

Storage-agnostic on purpose: the framework ships a reference in-memory ledger;
a deploying institution implements ``ConsentStore`` against their core system
(the adoption guide shows a SQLAlchemy example). No app coupling.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol


@dataclass(frozen=True)
class ConsentRecord:
    """
    An immutable consent event. Withdrawal is a *new* record, never a mutation —
    so the ledger is a complete, auditable history.
    """

    user_id: str
    purpose: str  # e.g. "cashflow_analysis", "thin_file_underwriting"
    granted: bool
    policy_version: str  # version of the consent/privacy notice agreed to
    timestamp: str  # ISO 8601; caller supplies (keeps this module clock-free)
    source: str = "app"  # where consent was captured (app, branch, phone, …)
    metadata: Dict[str, str] = field(default_factory=dict)


class ConsentStore(Protocol):
    """Interface an institution implements against its own datastore."""

    def append(self, record: ConsentRecord) -> None: ...

    def history(self, user_id: str, purpose: str) -> List[ConsentRecord]: ...


class InMemoryConsentStore:
    """Reference implementation for tests and demos (not for production)."""

    def __init__(self) -> None:
        self._records: List[ConsentRecord] = []

    def append(self, record: ConsentRecord) -> None:
        self._records.append(record)

    def history(self, user_id: str, purpose: str) -> List[ConsentRecord]:
        return [
            r for r in self._records if r.user_id == user_id and r.purpose == purpose
        ]


class ConsentService:
    """
    Consent decisions on top of any ``ConsentStore``.

    ``has_consent`` reflects the *latest* record for a (user, purpose): the most
    recent grant wins, a later withdrawal revokes it. This is what the execution
    policy / pipeline should call instead of assuming ``user_consent=True``.
    """

    def __init__(self, store: ConsentStore):
        self.store = store

    def record(self, record: ConsentRecord) -> None:
        self.store.append(record)

    def has_consent(self, user_id: str, purpose: str) -> bool:
        history = self.store.history(user_id, purpose)
        if not history:
            return False  # default-deny: no record means no consent
        latest = max(history, key=lambda r: r.timestamp)
        return latest.granted

    def latest(self, user_id: str, purpose: str) -> Optional[ConsentRecord]:
        history = self.store.history(user_id, purpose)
        return max(history, key=lambda r: r.timestamp) if history else None
