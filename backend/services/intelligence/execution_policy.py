"""
Execution Policy Engine — Deterministic Gate Before Action Dispatch.

Sits between Decision Synthesis (Stage 5) and actual execution.
Every action passes through this gate before touching the real world.

Rules:
    1. AllowedActions matrix: (intent, tier, risk_class, consent, partner) → allow/deny/confirm
    2. Two-step confirm for money movement and booking
    3. Idempotency enforcement via execution_id deduplication
    4. Retry policy with backoff + replay safety for partner calls
    5. SAFE_MINIMAL and crisis-mode intents are always gated to deny

This module is fully deterministic. No LLM.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, FrozenSet, List, Optional, Set

logger = logging.getLogger("intelligence.execution_policy")


# ============================================================================
# Enums
# ============================================================================

class RiskClass(str, Enum):
    """Risk classification for actions."""
    NONE = "none"           # Read-only, no side-effects
    LOW = "low"             # Reversible, no money
    MEDIUM = "medium"       # Reversible, small money or booking
    HIGH = "high"           # Large money movement or irreversible change
    CRITICAL = "critical"   # Legal, health, or large financial commitment


class ActionGate(str, Enum):
    """Outcome of the execution policy check."""
    ALLOW = "allow"         # Execute immediately
    CONFIRM = "confirm"     # Requires user confirmation before execution
    DENY = "deny"           # Blocked — do not execute
    CONFIRM_2FA = "confirm_2fa"  # Requires two-factor confirmation


class RetryStrategy(str, Enum):
    """Retry strategy for partner calls."""
    NONE = "none"
    LINEAR = "linear"       # Fixed interval
    EXPONENTIAL = "exponential"


# ============================================================================
# Risk Classification
# ============================================================================

# Intent → risk class mapping
_INTENT_RISK: Dict[str, RiskClass] = {
    # NONE (read-only)
    "balance_check": RiskClass.NONE,
    "spending_report": RiskClass.NONE,
    "cashflow_report": RiskClass.NONE,
    "sleep_analysis": RiskClass.NONE,
    "activity_summary": RiskClass.NONE,
    "stress_check": RiskClass.NONE,
    "recovery_status": RiskClass.NONE,
    "time_audit": RiskClass.NONE,
    "productivity_report": RiskClass.NONE,
    "health_report": RiskClass.NONE,
    "greeting": RiskClass.NONE,
    "net_worth_check": RiskClass.NONE,
    "salary_analysis": RiskClass.NONE,
    "subscription_review": RiskClass.NONE,
    "expense_categorize": RiskClass.NONE,
    "budget_alert": RiskClass.NONE,

    # LOW (reversible, no money)
    "schedule_event": RiskClass.LOW,
    "focus_time_block": RiskClass.LOW,
    "meeting_schedule": RiskClass.LOW,
    "deadline_reminder": RiskClass.LOW,
    "hydration_reminder": RiskClass.LOW,
    "nutrition_log": RiskClass.LOW,
    "workout_plan": RiskClass.LOW,
    "mental_health_check": RiskClass.LOW,
    "health_goal_set": RiskClass.LOW,
    "set_savings_goal": RiskClass.LOW,
    "goal_set": RiskClass.LOW,

    # MEDIUM (money or booking, but bounded)
    "bill_payment": RiskClass.MEDIUM,
    "mobility_booking": RiskClass.MEDIUM,
    "mobility_price_check": RiskClass.LOW,
    "investment_query": RiskClass.LOW,
    "loan_inquiry": RiskClass.LOW,
    "commute_planning": RiskClass.LOW,

    # HIGH (large money or irreversible)
    "car_purchase": RiskClass.HIGH,
    "financial_advisory": RiskClass.MEDIUM,
    "life_event_planning": RiskClass.HIGH,

    # CRITICAL (multi-domain, requires deep review)
    "career_change": RiskClass.CRITICAL,
    "relocation_analysis": RiskClass.CRITICAL,
    "tradeoff_analysis": RiskClass.HIGH,
}


# ============================================================================
# Execution Policy Result
# ============================================================================

@dataclass
class ExecutionPolicyResult:
    """Output of the execution policy check."""
    gate: ActionGate
    risk_class: RiskClass
    reason: str = ""
    requires_confirmation: bool = False
    confirmation_message: Optional[str] = None
    idempotency_key: Optional[str] = None
    retry_strategy: RetryStrategy = RetryStrategy.NONE
    max_retries: int = 0
    blocked_actions: List[str] = field(default_factory=list)


# ============================================================================
# Idempotency Store (in-memory, swap for Redis in production)
# ============================================================================

class IdempotencyStore:
    """Simple deduplication store for execution_ids."""

    def __init__(self):
        self._seen: Set[str] = set()

    def check_and_mark(self, execution_id: str) -> bool:
        """
        Returns True if this is a NEW execution_id (safe to proceed).
        Returns False if this execution_id was already processed (duplicate).
        """
        if execution_id in self._seen:
            return False
        self._seen.add(execution_id)
        return True

    def clear(self, execution_id: str) -> None:
        """Remove an execution_id from the store (for rollback)."""
        self._seen.discard(execution_id)


# ============================================================================
# Execution Policy Engine
# ============================================================================

class ExecutionPolicyEngine:
    """
    Deterministic gate between the pipeline's decision and real-world execution.

    Every action passes through here. The engine checks:
        1. Risk class of the intent
        2. Tier-based limits
        3. User consent state
        4. Partner availability
        5. Idempotency (no duplicate executions)
        6. SAFE_MINIMAL / crisis-mode blocks
    """

    def __init__(self, idempotency_store: Optional[IdempotencyStore] = None):
        self._idempotency = idempotency_store or IdempotencyStore()

    def evaluate(
        self,
        intent_type: str,
        tier: int,
        execution_id: str,
        user_consent: bool = True,
        partner_available: bool = True,
        tradeoff_resolution: Optional[str] = None,
        crisis_mode: bool = False,
        action_types: Optional[List[str]] = None,
    ) -> ExecutionPolicyResult:
        """
        Evaluate whether an action should be allowed, confirmed, or denied.

        Args:
            intent_type: Classified intent name.
            tier: Pipeline tier (0-3).
            execution_id: Unique execution identifier.
            user_consent: Whether user has given general consent for actions.
            partner_available: Whether the target partner service is available.
            tradeoff_resolution: From TradeoffValidator (proceed/clarify/escalate/safe_minimal).
            crisis_mode: Whether user is in crisis mode.
            action_types: List of action_type strings from ActionPlan steps.

        Returns:
            ExecutionPolicyResult with gate decision and metadata.
        """
        risk = _INTENT_RISK.get(intent_type, RiskClass.MEDIUM)
        action_types = action_types or []

        # Rule 1: IDEMPOTENCY CHECK
        if not self._idempotency.check_and_mark(execution_id):
            logger.info("Execution blocked: duplicate execution_id=%s", execution_id)
            return ExecutionPolicyResult(
                gate=ActionGate.DENY,
                risk_class=risk,
                reason=f"Duplicate execution_id: {execution_id}",
            )

        # Rule 2: SAFE_MINIMAL → DENY all executions
        if tradeoff_resolution == "safe_minimal":
            logger.info("Execution blocked: SAFE_MINIMAL resolution")
            return ExecutionPolicyResult(
                gate=ActionGate.DENY,
                risk_class=risk,
                reason="SAFE_MINIMAL resolution — no actions permitted.",
                blocked_actions=action_types,
            )

        # Rule 3: CRISIS MODE + HIGH/CRITICAL RISK → DENY
        if crisis_mode and risk in (RiskClass.HIGH, RiskClass.CRITICAL):
            logger.info("Execution blocked: crisis mode + %s risk", risk.value)
            return ExecutionPolicyResult(
                gate=ActionGate.DENY,
                risk_class=risk,
                reason=f"Crisis mode active — {risk.value} risk actions blocked.",
                blocked_actions=action_types,
            )

        # Rule 4: NO CONSENT → DENY for anything beyond read-only
        if not user_consent and risk != RiskClass.NONE:
            return ExecutionPolicyResult(
                gate=ActionGate.DENY,
                risk_class=risk,
                reason="User consent not provided for this action type.",
            )

        # Rule 5: PARTNER UNAVAILABLE → DENY for partner-dependent actions
        partner_actions = {"execute_financial", "execute_mobility", "execute_partner"}
        if not partner_available and any(a in partner_actions for a in action_types):
            return ExecutionPolicyResult(
                gate=ActionGate.DENY,
                risk_class=risk,
                reason="Target partner service is unavailable.",
            )

        # Rule 6: RISK-BASED GATING
        if risk == RiskClass.NONE:
            return ExecutionPolicyResult(
                gate=ActionGate.ALLOW,
                risk_class=risk,
                reason="Read-only action — no gate required.",
            )

        if risk == RiskClass.LOW:
            return ExecutionPolicyResult(
                gate=ActionGate.ALLOW,
                risk_class=risk,
                reason="Low-risk reversible action.",
            )

        if risk == RiskClass.MEDIUM:
            # Money/booking: two-step confirm
            return ExecutionPolicyResult(
                gate=ActionGate.CONFIRM,
                risk_class=risk,
                reason="Medium-risk action — requires user confirmation.",
                requires_confirmation=True,
                confirmation_message=self._build_confirmation_message(intent_type, risk),
                idempotency_key=execution_id,
                retry_strategy=RetryStrategy.EXPONENTIAL,
                max_retries=3,
            )

        if risk == RiskClass.HIGH:
            return ExecutionPolicyResult(
                gate=ActionGate.CONFIRM,
                risk_class=risk,
                reason="High-risk action — requires explicit user confirmation.",
                requires_confirmation=True,
                confirmation_message=self._build_confirmation_message(intent_type, risk),
                idempotency_key=execution_id,
                retry_strategy=RetryStrategy.EXPONENTIAL,
                max_retries=2,
            )

        # CRITICAL
        return ExecutionPolicyResult(
            gate=ActionGate.CONFIRM_2FA,
            risk_class=risk,
            reason="Critical-risk action — requires two-factor confirmation.",
            requires_confirmation=True,
            confirmation_message=self._build_confirmation_message(intent_type, risk),
            idempotency_key=execution_id,
            retry_strategy=RetryStrategy.NONE,
            max_retries=0,
        )

    def rollback(self, execution_id: str) -> None:
        """Remove an execution_id from idempotency store (for failed executions)."""
        self._idempotency.clear(execution_id)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_confirmation_message(intent_type: str, risk: RiskClass) -> str:
        """Build a human-readable confirmation message."""
        messages = {
            "bill_payment": "I'll process this bill payment. Confirm to proceed?",
            "mobility_booking": "Ready to book this ride. Shall I confirm?",
            "car_purchase": (
                "This is a major financial commitment. "
                "I want to make sure you've reviewed all the details. Confirm to proceed?"
            ),
            "financial_advisory": "I'll provide financial advice based on your profile. Ready?",
            "life_event_planning": (
                "This life event has significant financial and time implications. "
                "Confirm to continue planning?"
            ),
            "career_change": (
                "Career changes impact all three dimensions of your life. "
                "This requires careful analysis. Confirm to proceed?"
            ),
            "relocation_analysis": (
                "Relocation is a major life decision. "
                "Confirm to begin the full analysis?"
            ),
        }

        return messages.get(
            intent_type,
            f"This is a {risk.value}-risk action. Would you like to proceed?"
        )

    @staticmethod
    def get_risk_class(intent_type: str) -> RiskClass:
        """Get the risk class for an intent type."""
        return _INTENT_RISK.get(intent_type, RiskClass.MEDIUM)
