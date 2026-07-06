"""
Portable execution policy engine — the human-in-the-loop / consent gate.

Config-driven and deterministic, in the same spirit as the AssessmentEngine:
per-action policy is *data*. Given an action + context it returns a gate
decision (ALLOW / CONFIRM / CONFIRM_2FA / DENY) with a reason, enforcing:

  * **Default-deny** — an unknown, non-read-only action is denied.
  * **Consent-gated** — actions needing consent are denied unless a matching
    grant is on file (via ConsentService).
  * **Risk-tiered** — higher risk requires confirmation / step-up (2FA).
  * **Safe-mode** — in a crisis/degraded context, only read-only actions pass.
  * **Idempotent** — an already-seen request is denied as a duplicate.

Every decision can be written to an append-only, tamper-evident decision log.
The engine never executes anything; it only authorizes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntEnum
from typing import Dict, Optional


class RiskClass(IntEnum):
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


# Gate decisions, most to least permissive.
ALLOW = "ALLOW"
CONFIRM = "CONFIRM"
CONFIRM_2FA = "CONFIRM_2FA"
DENY = "DENY"


@dataclass(frozen=True)
class ActionPolicy:
    """Declarative policy for one action type."""

    risk_class: RiskClass = RiskClass.MEDIUM
    read_only: bool = False  # read-only actions never need consent/confirmation
    requires_consent: bool = False
    consent_purpose: Optional[str] = None  # purpose key checked against consent


@dataclass
class PolicyConfig:
    """Per-action policies + how each risk class maps to a gate decision."""

    actions: Dict[str, ActionPolicy] = field(default_factory=dict)
    # Risk -> gate decision. Secure defaults; override per deployment.
    risk_gates: Dict[RiskClass, str] = field(
        default_factory=lambda: {
            RiskClass.NONE: ALLOW,
            RiskClass.LOW: ALLOW,
            RiskClass.MEDIUM: CONFIRM,
            RiskClass.HIGH: CONFIRM_2FA,
            RiskClass.CRITICAL: CONFIRM_2FA,
        }
    )
    # What to do with an action that has no policy entry. Default: deny.
    default_deny_unknown: bool = True


@dataclass
class PolicyResult:
    action: str
    decision: str
    risk_class: Optional[RiskClass]
    reason: str

    @property
    def allowed(self) -> bool:
        return self.decision == ALLOW

    @property
    def requires_confirmation(self) -> bool:
        return self.decision in (CONFIRM, CONFIRM_2FA)

    @property
    def requires_2fa(self) -> bool:
        return self.decision == CONFIRM_2FA


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ExecutionPolicy:
    """Deterministic authorization gate. Stateless except injected stores."""

    def __init__(
        self,
        config: PolicyConfig,
        consent_service=None,  # ConsentService (optional)
        decision_log=None,  # SqlDecisionLog (optional)
        idempotency_store=None,  # SqlIdempotencyStore (optional)
    ):
        self.config = config
        self.consent = consent_service
        self.decision_log = decision_log
        self.idempotency = idempotency_store

    def evaluate(
        self,
        action: str,
        subject_id: str,
        context: Optional[Dict] = None,
        *,
        timestamp: Optional[str] = None,
        correlation_id: Optional[str] = None,
    ) -> PolicyResult:
        context = context or {}
        ts = timestamp or _utc_now_iso()
        result = self._decide(action, subject_id, context)
        self._log(result, subject_id, ts, correlation_id, context)
        return result

    # -- core decision logic (deterministic) -------------------------------

    def _decide(self, action: str, subject_id: str, context: Dict) -> PolicyResult:
        policy = self.config.actions.get(action)

        # 1. Unknown action → default-deny (unless configured otherwise).
        if policy is None:
            if self.config.default_deny_unknown:
                return PolicyResult(
                    action, DENY, None, "Unknown action — denied by default."
                )
            policy = ActionPolicy()  # permissive fallback if explicitly configured

        # 2. Read-only actions are always allowed (no consent/confirmation).
        if policy.read_only:
            return PolicyResult(action, ALLOW, policy.risk_class, "Read-only action.")

        # 3. Safe/crisis mode: block anything that isn't read-only.
        if context.get("safe_mode") or context.get("crisis_mode"):
            return PolicyResult(
                action,
                DENY,
                policy.risk_class,
                "Safe-mode active — only read-only actions permitted.",
            )

        # 4. Consent gate → deny if required consent is absent.
        if policy.requires_consent:
            purpose = policy.consent_purpose or action
            if self.consent is None or not self.consent.has_consent(
                subject_id, purpose
            ):
                return PolicyResult(
                    action,
                    DENY,
                    policy.risk_class,
                    f"No consent on file for purpose '{purpose}'.",
                )

        # 5. Risk-tiered gate.
        decision = self.config.risk_gates.get(policy.risk_class, DENY)
        reason = {
            ALLOW: "Low-risk action authorized.",
            CONFIRM: "Requires explicit user confirmation.",
            CONFIRM_2FA: "High-risk — requires confirmation with step-up (2FA).",
            DENY: "Denied by risk policy.",
        }[decision]

        # 6. Idempotency is consumed ONLY when we would authorize execution.
        #    Consuming it earlier (e.g. on a CONFIRM) would block the user's
        #    legitimate follow-up confirmation as a "duplicate".
        if decision == ALLOW:
            idem_key = context.get("idempotency_key")
            if idem_key and self.idempotency is not None:
                is_new = self.idempotency.register(idem_key, context.get("_ts", ""))
                if not is_new:
                    return PolicyResult(
                        action,
                        DENY,
                        policy.risk_class,
                        "Duplicate request — already processed.",
                    )

        return PolicyResult(action, decision, policy.risk_class, reason)

    def _log(self, result: PolicyResult, subject_id, ts, correlation_id, context):
        if self.decision_log is None:
            return
        try:
            self.decision_log.append(
                timestamp=ts,
                subject_id=subject_id,
                action=result.action,
                decision=result.decision,
                risk_class=result.risk_class.name if result.risk_class else None,
                reason=result.reason,
                correlation_id=correlation_id,
                metadata={"safe_mode": bool(context.get("safe_mode"))},
            )
        except Exception:
            # Logging must never break the gate; the decision already stands.
            pass
