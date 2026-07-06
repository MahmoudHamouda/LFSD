"""
Operational tests for the DB-backed governance layer: consent persistence,
tamper-evidence, the policy gate, idempotency, and PII hardening.

    python -m pytest responsible_ai/tests/test_governance_db.py -q
"""

from sqlalchemy import create_engine, text, update
from sqlalchemy.pool import StaticPool

from responsible_ai.governance import (
    ConsentRecord,
    ConsentService,
    ExecutionPolicy,
    PolicyConfig,
    ActionPolicy,
    RiskClass,
    ALLOW,
    CONFIRM,
    CONFIRM_2FA,
    DENY,
    PIIRedactor,
    log_redaction,
    luhn_valid,
)
from responsible_ai.governance import stores as st


def _engine():
    """Shared in-memory SQLite (StaticPool keeps one connection alive)."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    st.create_all(engine)
    return engine


# -- consent persistence ----------------------------------------------------


def test_consent_db_roundtrip_and_default_deny():
    svc = ConsentService(st.SqlConsentStore(_engine()))
    assert svc.has_consent("u1", "cashflow") is False  # default-deny
    svc.record(ConsentRecord("u1", "cashflow", True, "v1", "2026-01-01T00:00:00"))
    assert svc.has_consent("u1", "cashflow") is True
    svc.record(ConsentRecord("u1", "cashflow", False, "v1", "2026-02-01T00:00:00"))
    assert svc.has_consent("u1", "cashflow") is False  # latest withdrawal wins
    assert len(svc.store.history("u1", "cashflow")) == 2  # append-only, nothing lost


def test_consent_chain_detects_tampering():
    engine = _engine()
    store = st.SqlConsentStore(engine)
    store.append(ConsentRecord("u1", "p", True, "v1", "2026-01-01T00:00:00"))
    store.append(ConsentRecord("u1", "p", False, "v1", "2026-02-01T00:00:00"))
    assert store.verify_chain() is True
    # Silently flip a granted flag directly in the DB.
    with engine.begin() as conn:
        conn.execute(
            update(st.consent_records)
            .where(st.consent_records.c.id == 1)
            .values(granted=False)
        )
    assert store.verify_chain() is False  # tamper detected


# -- policy gate ------------------------------------------------------------


def _policy(**kw):
    engine = _engine()
    config = PolicyConfig(
        actions={
            "view_balance": ActionPolicy(risk_class=RiskClass.NONE, read_only=True),
            "move_money": ActionPolicy(
                risk_class=RiskClass.MEDIUM,
                requires_consent=True,
                consent_purpose="payments",
            ),
            "close_account": ActionPolicy(risk_class=RiskClass.CRITICAL),
            # A low-risk, executable (ALLOW-tier) action for idempotency tests.
            "log_feedback": ActionPolicy(risk_class=RiskClass.LOW),
        }
    )
    consent = ConsentService(st.SqlConsentStore(engine))
    return (
        ExecutionPolicy(
            config,
            consent_service=consent,
            decision_log=st.SqlDecisionLog(engine),
            idempotency_store=st.SqlIdempotencyStore(engine),
        ),
        consent,
        engine,
    )


def test_unknown_action_default_denied():
    eng, _, _ = _policy()
    assert eng.evaluate("hack_the_bank", "u1").decision == DENY


def test_read_only_allowed():
    eng, _, _ = _policy()
    assert eng.evaluate("view_balance", "u1").decision == ALLOW


def test_consent_required_denies_without_grant_then_confirms():
    eng, consent, _ = _policy()
    assert eng.evaluate("move_money", "u1").decision == DENY  # no consent
    consent.record(ConsentRecord("u1", "payments", True, "v1", "2026-01-01T00:00:00"))
    assert eng.evaluate("move_money", "u1").decision == CONFIRM  # MEDIUM → confirm


def test_critical_requires_2fa():
    eng, _, _ = _policy()
    assert eng.evaluate("close_account", "u1").decision == CONFIRM_2FA


def test_safe_mode_blocks_non_readonly():
    eng, _, _ = _policy()
    assert eng.evaluate("close_account", "u1", {"safe_mode": True}).decision == DENY
    assert eng.evaluate("view_balance", "u1", {"safe_mode": True}).decision == ALLOW


def test_idempotency_consumed_only_on_allow():
    eng, _, _ = _policy()
    ctx = {"idempotency_key": "req-123"}
    first = eng.evaluate("log_feedback", "u1", ctx)  # ALLOW → consumes the key
    second = eng.evaluate("log_feedback", "u1", ctx)  # duplicate → denied
    assert first.decision == ALLOW and second.decision == DENY


def test_confirm_flow_not_blocked_by_idempotency():
    """A CONFIRM must not burn the key, so the follow-up confirmation survives."""
    eng, consent, _ = _policy()
    consent.record(ConsentRecord("u1", "payments", True, "v1", "2026-01-01T00:00:00"))
    ctx = {"idempotency_key": "req-999"}
    first = eng.evaluate("move_money", "u1", ctx)
    second = eng.evaluate("move_money", "u1", ctx)
    assert first.decision == CONFIRM and second.decision == CONFIRM


def test_decisions_are_logged_and_chained():
    eng, _, engine = _policy()
    eng.evaluate("view_balance", "u1")
    eng.evaluate("close_account", "u1")
    log = st.SqlDecisionLog(engine)
    assert len(log.recent()) == 2
    assert log.verify_chain() is True


# -- PII hardening ----------------------------------------------------------


def test_luhn():
    assert luhn_valid("4111111111111111") is True  # test Visa
    assert luhn_valid("4111111111111112") is False


def test_account_and_identifiers_redacted():
    r = PIIRedactor().redact_text(
        "card 4111 1111 1111 1111 acct 12345678901234 ssn 123-45-6789 a@b.com"
    )
    assert r.counts.get("ACCOUNT", 0) >= 2
    assert "SSN" in r.counts and "EMAIL" in r.counts
    assert "4111" not in r.text and "123-45-6789" not in r.text


def test_redactor_is_redos_safe_on_adversarial_input():
    # Long run of digits/spaces that would blow up a backtracking regex.
    evil = ("1 " * 5000) + "!"
    report = PIIRedactor().redact_text(evil)  # must return promptly, not hang
    assert isinstance(report.text, str)


def test_log_redaction_records_counts_not_raw_text():
    engine = _engine()
    log = st.SqlDecisionLog(engine)
    report = PIIRedactor().redact_text("ssn 123-45-6789")
    log_redaction(log, subject_id="u1", report=report, timestamp="2026-01-01T00:00:00")
    rows = log.recent()
    assert rows and rows[0]["action"] == "pii_redaction"
    assert "123-45-6789" not in (rows[0]["metadata_json"] or "")
