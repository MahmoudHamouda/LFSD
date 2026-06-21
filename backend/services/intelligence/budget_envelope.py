"""
Per-User Budget Envelopes — Dynamic Tier Limits Based on User State.

Instead of flat per-tier budgets, this module adjusts token limits and
CLARIFY probability based on the user's current state:

    - Crisis mode → force Tier ≤ 2 unless review overrides
    - Power user / paid plan → allow higher T2/T3 frequency
    - High volatility week → increase CLARIFY probability
    - Per-user overrides via profile configuration

Fully deterministic. No LLM. Sub-millisecond.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger("intelligence.budget_envelope")


class UserPlan(str, Enum):
    """User subscription plan tier."""

    FREE = "free"
    STANDARD = "standard"
    PREMIUM = "premium"


@dataclass
class BudgetEnvelope:
    """
    Per-user tier and token budget configuration.

    Applied at the start of each pipeline run to constrain the tier router.
    """

    max_tier: int = 3  # Maximum allowed tier
    max_input_tokens: int = 2000  # Total input token budget per request
    max_output_tokens: int = 500  # Total output token budget per request
    clarify_confidence_boost: float = (
        0.0  # Added to CLARIFY threshold (higher = more CLARIFYs)
    )
    force_deterministic: bool = False  # If True, skip all LLM calls
    reason: str = ""  # Why this envelope was chosen


class BudgetEnvelopeEngine:
    """
    Computes the budget envelope for a user given their current state.

    Inputs: user plan, crisis mode, volatility signals, explicit overrides.
    Output: BudgetEnvelope constraining the pipeline's tier and token usage.
    """

    def compute(
        self,
        user_plan: UserPlan = UserPlan.FREE,
        crisis_mode: bool = False,
        crisis_dimensions: Optional[list] = None,
        high_volatility: bool = False,
        explicit_max_tier: Optional[int] = None,
        explicit_force_deterministic: Optional[bool] = None,
    ) -> BudgetEnvelope:
        """
        Compute the budget envelope for this request.

        Priority order:
            1. Explicit overrides (from user profile / admin)
            2. Crisis mode constraints
            3. Volatility adjustments
            4. Plan-based limits
        """
        reasons = []

        # Start with plan-based defaults
        envelope = self._plan_defaults(user_plan)

        # Apply crisis mode constraints
        if crisis_mode:
            envelope = self._apply_crisis_constraints(envelope, crisis_dimensions or [])
            reasons.append("crisis_mode")

        # Apply volatility adjustments
        if high_volatility:
            envelope = self._apply_volatility_boost(envelope)
            reasons.append("high_volatility")

        # Apply explicit overrides (highest priority)
        if explicit_max_tier is not None:
            envelope.max_tier = explicit_max_tier
            reasons.append(f"explicit_max_tier={explicit_max_tier}")

        if explicit_force_deterministic is not None:
            envelope.force_deterministic = explicit_force_deterministic
            if explicit_force_deterministic:
                envelope.max_tier = 0
                reasons.append("force_deterministic")

        envelope.reason = "; ".join(reasons) if reasons else f"plan={user_plan.value}"

        logger.info(
            "Budget envelope: max_tier=%d tokens=%d/%d clarify_boost=%.2f reason=%s",
            envelope.max_tier,
            envelope.max_input_tokens,
            envelope.max_output_tokens,
            envelope.clarify_confidence_boost,
            envelope.reason,
        )

        return envelope

    # ------------------------------------------------------------------
    # Plan Defaults
    # ------------------------------------------------------------------

    @staticmethod
    def _plan_defaults(plan: UserPlan) -> BudgetEnvelope:
        """Base budget envelope per subscription plan."""
        if plan == UserPlan.FREE:
            return BudgetEnvelope(
                max_tier=2,
                max_input_tokens=800,
                max_output_tokens=200,
            )
        if plan == UserPlan.STANDARD:
            return BudgetEnvelope(
                max_tier=3,
                max_input_tokens=2000,
                max_output_tokens=500,
            )
        # PREMIUM
        return BudgetEnvelope(
            max_tier=3,
            max_input_tokens=4000,
            max_output_tokens=1000,
        )

    # ------------------------------------------------------------------
    # Crisis Constraints
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_crisis_constraints(
        envelope: BudgetEnvelope, crisis_dimensions: list
    ) -> BudgetEnvelope:
        """
        Crisis mode → cap tier at 2 and reduce token budgets.

        Rationale: in crisis, we want fast, predictable responses.
        Heavy LLM is only allowed if explicitly overridden.
        """
        envelope.max_tier = min(envelope.max_tier, 2)
        envelope.max_input_tokens = min(envelope.max_input_tokens, 800)
        envelope.max_output_tokens = min(envelope.max_output_tokens, 200)

        # If multiple dimensions in crisis, increase CLARIFY threshold
        if len(crisis_dimensions) >= 2:
            envelope.clarify_confidence_boost += 0.10

        return envelope

    # ------------------------------------------------------------------
    # Volatility Adjustments
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_volatility_boost(envelope: BudgetEnvelope) -> BudgetEnvelope:
        """
        High volatility week → increase CLARIFY probability.

        When the user's data is changing rapidly (many transactions,
        score fluctuations), we want to ask more clarifying questions
        rather than making assumptions.
        """
        envelope.clarify_confidence_boost += 0.15
        return envelope
