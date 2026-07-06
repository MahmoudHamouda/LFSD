"""
App-side adapter for the standalone Responsible-AI governance layer.

The ``responsible_ai`` package is a portable, top-level library (it imports
nothing from this app). This bridge is the *only* place the app couples to it:
it constructs the governance services on the app's database engine and exposes a
small, safe surface to the pipeline.

Everything here is gated by ``settings.RAI_GOVERNANCE_ENABLED``. When disabled,
the bridge is a no-op (consent always granted, no redaction). It can be turned
off at runtime by setting ``RAI_GOVERNANCE_ENABLED=false`` — no code change.

Failure policy: if governance is enabled but the layer can't initialize, calls
fail **closed** (consent denied, action denied) rather than silently skipping.
"""

from __future__ import annotations

import functools
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import core.config

logger = logging.getLogger("governance_bridge")


# Whole-word triggers indicating the request needs the user's financial data —
# only these require consent. A greeting ("Hi") or a health/time question does
# not. Tuned to catch real financial questions without over-prompting.
_FINANCIAL_TRIGGERS = [
    "spend",
    "spent",
    "spending",
    "budget",
    "afford",
    "affordability",
    "balance",
    "save",
    "saving",
    "savings",
    "invest",
    "investment",
    "investments",
    "debt",
    "loan",
    "loans",
    "income",
    "expense",
    "expenses",
    "mortgage",
    "retirement",
    "net worth",
    "money",
    "financial",
    "finance",
    "salary",
    "wealth",
    "portfolio",
    "bill",
    "bills",
    "buy",
    "purchase",
    "cash flow",
    "cashflow",
]
_FINANCIAL_RE = re.compile(
    r"\b(?:" + "|".join(re.escape(k) for k in _FINANCIAL_TRIGGERS) + r")\b",
    re.IGNORECASE,
)


def enabled() -> bool:
    return bool(getattr(core.config.get_settings(), "RAI_GOVERNANCE_ENABLED", False))


def needs_financial_consent(text: str) -> bool:
    """True when a message asks about the user's finances (consent-gated)."""
    return bool(text) and bool(_FINANCIAL_RE.search(text))


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_importable() -> None:
    """Make ``responsible_ai`` importable in dev (it lives at the repo root, the
    parent of this backend/ dir). In the container it is vendored alongside the
    app, so the plain import already resolves."""
    try:
        import responsible_ai  # noqa: F401

        return
    except ImportError:
        repo_root = Path(__file__).resolve().parents[2]
        if str(repo_root) not in sys.path:
            sys.path.insert(0, str(repo_root))


@functools.lru_cache(maxsize=1)
def _components():
    """Build governance services once, on the app's engine. Cached per process."""
    _ensure_importable()
    from responsible_ai.governance import (
        ActionPolicy,
        ConsentService,
        ExecutionPolicy,
        PIIRedactor,
        PolicyConfig,
        RiskClass,
    )
    from responsible_ai.governance import stores as st
    from models.database import engine

    st.create_all(engine)  # idempotent; provisions rai_* tables

    consent = ConsentService(st.SqlConsentStore(engine))
    decisions = st.SqlDecisionLog(engine)
    policy = ExecutionPolicy(
        PolicyConfig(
            actions={
                # AI advisory is a read/generate action, consent-gated.
                "ai_advisory": ActionPolicy(
                    risk_class=RiskClass.LOW,
                    requires_consent=True,
                    consent_purpose=core.config.get_settings().RAI_CONSENT_PURPOSE,
                ),
            }
        ),
        consent_service=consent,
        decision_log=decisions,
        idempotency_store=st.SqlIdempotencyStore(engine),
    )
    return {
        "consent": consent,
        "decisions": decisions,
        "redactor": PIIRedactor(),
        "policy": policy,
        "ConsentRecord": _import_consent_record(),
    }


def _import_consent_record():
    _ensure_importable()
    from responsible_ai.governance import ConsentRecord

    return ConsentRecord


# ---------------------------------------------------------------------------
# Public surface (all no-ops / fail-closed when disabled)
# ---------------------------------------------------------------------------


def has_consent(user_id: str, purpose: Optional[str] = None) -> bool:
    if not enabled():
        return True  # governance off → do not block
    purpose = purpose or core.config.get_settings().RAI_CONSENT_PURPOSE
    try:
        return _components()["consent"].has_consent(user_id, purpose)
    except Exception as e:  # fail closed
        logger.error("Consent check failed; denying: %s", e)
        return False


def record_consent(
    user_id: str,
    granted: bool,
    purpose: Optional[str] = None,
    source: str = "app",
) -> None:
    settings = core.config.get_settings()
    purpose = purpose or settings.RAI_CONSENT_PURPOSE
    comps = _components()
    comps["consent"].record(
        comps["ConsentRecord"](
            user_id=user_id,
            purpose=purpose,
            granted=granted,
            policy_version=settings.RAI_CONSENT_POLICY_VERSION,
            timestamp=_utc_now_iso(),
            source=source,
        )
    )


def redact(text: str) -> str:
    """Redact direct identifiers from text before it can reach an LLM."""
    if not enabled() or not text:
        return text
    try:
        return _components()["redactor"].redact_text(text).text
    except Exception as e:
        # Fail closed for PII: if redaction breaks, prefer masking everything.
        logger.error("Redaction failed; masking whole payload: %s", e)
        return "[REDACTED]"


def log_decision(user_id: str, action: str, decision: str, reason: str) -> None:
    if not enabled():
        return
    try:
        _components()["decisions"].append(
            timestamp=_utc_now_iso(),
            subject_id=user_id,
            action=action,
            decision=decision,
            reason=reason,
        )
    except Exception as e:
        logger.error("Decision log append failed (non-fatal): %s", e)


def consent_required_message(purpose: Optional[str] = None) -> str:
    return (
        "To answer questions about your finances, I need your consent to "
        "analyze your financial data. Tap **I consent** below to continue — "
        "you can withdraw it at any time."
    )
