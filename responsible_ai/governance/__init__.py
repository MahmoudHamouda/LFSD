"""Governance controls: PII redaction, consent, policy gate, and fair-lending.

Pure logic (consent, pii, fairness, policy) has no third-party dependency.
The DB-backed stores (``stores``) require SQLAlchemy and are imported lazily so
the rest of the package stays dependency-light.
"""

from .consent import (
    ConsentRecord,
    ConsentService,
    ConsentStore,
    InMemoryConsentStore,
)
from .fairness import (
    AdverseActionReason,
    AdverseActionReasoner,
    DisparateImpactResult,
    four_fifths_check,
)
from .pii import (
    DEFAULT_FINANCIAL_ALLOWLIST,
    PIIRedactor,
    RedactionReport,
    log_redaction,
    luhn_valid,
)
from .policy import (
    ActionPolicy,
    ExecutionPolicy,
    PolicyConfig,
    PolicyResult,
    RiskClass,
    ALLOW,
    CONFIRM,
    CONFIRM_2FA,
    DENY,
)

__all__ = [
    # PII
    "PIIRedactor",
    "RedactionReport",
    "DEFAULT_FINANCIAL_ALLOWLIST",
    "log_redaction",
    "luhn_valid",
    # Consent
    "ConsentRecord",
    "ConsentService",
    "ConsentStore",
    "InMemoryConsentStore",
    # Fairness
    "AdverseActionReasoner",
    "AdverseActionReason",
    "four_fifths_check",
    "DisparateImpactResult",
    # Policy
    "ExecutionPolicy",
    "PolicyConfig",
    "ActionPolicy",
    "PolicyResult",
    "RiskClass",
    "ALLOW",
    "CONFIRM",
    "CONFIRM_2FA",
    "DENY",
]


def __getattr__(name):
    """Lazily expose the SQLAlchemy-backed stores without importing SQLAlchemy
    eagerly (keeps pure-logic imports dependency-free)."""
    store_names = {
        "SqlConsentStore",
        "SqlDecisionLog",
        "SqlIdempotencyStore",
        "create_all",
    }
    if name in store_names:
        from . import stores

        return getattr(stores, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
