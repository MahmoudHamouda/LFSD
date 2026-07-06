"""
Runnable demo: the governance layer operating on its own against a database.

    python -m responsible_ai.governance.demo

Uses an in-memory SQLite DB to show consent persistence, the policy gate,
tamper-evidence, and audited PII redaction — with no application involved.
"""

from __future__ import annotations

from sqlalchemy import create_engine, update
from sqlalchemy.pool import StaticPool

from . import stores as st
from .consent import ConsentRecord, ConsentService
from .pii import PIIRedactor, log_redaction
from .policy import ActionPolicy, ExecutionPolicy, PolicyConfig, RiskClass


def _engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    st.create_all(engine)
    return engine


def main() -> None:
    engine = _engine()
    consent = ConsentService(st.SqlConsentStore(engine))
    log = st.SqlDecisionLog(engine)
    gate = ExecutionPolicy(
        PolicyConfig(
            actions={
                "view_balance": ActionPolicy(RiskClass.NONE, read_only=True),
                "move_money": ActionPolicy(
                    RiskClass.MEDIUM, requires_consent=True, consent_purpose="payments"
                ),
                "close_account": ActionPolicy(RiskClass.CRITICAL),
            }
        ),
        consent_service=consent,
        decision_log=log,
        idempotency_store=st.SqlIdempotencyStore(engine),
    )

    print("=" * 66)
    print("GOVERNANCE LAYER — standalone, DB-backed")
    print("=" * 66)

    print("\n[policy gate]")
    for action, ctx in [
        ("view_balance", {}),
        ("move_money", {}),  # denied: no consent yet
        ("close_account", {}),
    ]:
        r = gate.evaluate(action, "u1", ctx)
        print(f"  {action:14} -> {r.decision:12} ({r.reason})")

    print("\n[consent] grant 'payments', retry move_money")
    consent.record(ConsentRecord("u1", "payments", True, "v1", "2026-01-01T00:00:00"))
    r = gate.evaluate("move_money", "u1")
    print(f"  move_money     -> {r.decision:12} ({r.reason})")

    print("\n[pii] redact + audit (counts only)")
    report = PIIRedactor().redact_text(
        "wire from acct 4111 1111 1111 1111, ssn 123-45-6789"
    )
    log_redaction(log, subject_id="u1", report=report, timestamp="2026-01-01T00:01:00")
    print(f"  redacted text: {report.text}")
    print(f"  counts:        {report.counts}")

    print("\n[audit] decision log is append-only + hash-chained")
    print(f"  entries:       {len(log.recent())}")
    print(f"  chain valid:   {log.verify_chain()}")

    # Tamper with a row (flip the first DENY into an ALLOW) — the chain breaks.
    with engine.begin() as conn:
        conn.execute(
            update(st.decision_log)
            .where(st.decision_log.c.decision == "DENY")
            .values(decision="ALLOW")
        )
    valid = log.verify_chain()
    print(
        f"  after tamper:  chain valid = {valid}  "
        f"({'tamper detected' if not valid else 'NOT detected!'})"
    )


if __name__ == "__main__":
    main()
