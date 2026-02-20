"""
Tradeoff Validator — Deterministic Contradiction Detector (Stage 4.5).

Sits between Score Evaluation (Stage 4) and Decision Synthesis (Stage 5).
Inspects ScoreDeltas for contradictions and forces one of:
    - PROCEED:        No contradictions; continue to synthesis.
    - CLARIFY:        Missing ONE scalar — ask user for it.
    - ESCALATE:       Multi-variable reasoning needed — heavy LLM.
    - SAFE_MINIMAL:   Risky tradeoff — compliance-safe minimal response.

SAFE_MINIMAL Product Contract:
    ✓ No spending commitments
    ✓ No irreversible actions
    ✓ Only reversible suggestions + stabilization steps
    ✓ Exactly 1 safe next action + 1 clarifying question
    ✓ Defensible for compliance audit

Entirely deterministic. No LLM. Sub-millisecond.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import FrozenSet, List, Optional, Set

from .schemas import ContextFrame, IntentResult, ScoreDeltas

logger = logging.getLogger("intelligence.tradeoff_validator")


class TradeoffResolution(str, Enum):
    """Possible outcomes of tradeoff validation."""
    PROCEED = "proceed"
    CLARIFY = "clarify"
    ESCALATE = "escalate"
    SAFE_MINIMAL = "safe_minimal"


# ============================================================================
# SAFE_MINIMAL Product Contract
# ============================================================================

@dataclass
class SafeMinimalContract:
    """
    Compliance-ready contract for SAFE_MINIMAL responses.

    Every SAFE_MINIMAL resolution MUST populate this contract.
    Invariants:
        - no_spending_commitments is always True
        - no_irreversible_actions is always True
        - only_reversible_suggestions is always True
        - offer_one_next_action is always non-empty
        - offer_one_question is always non-empty
    """
    no_spending_commitments: bool = True
    no_irreversible_actions: bool = True
    only_reversible_suggestions: bool = True
    offer_one_next_action: str = ""
    offer_one_question: str = ""
    stabilization_steps: List[str] = field(default_factory=list)

    def validate(self) -> bool:
        """Assert all invariants hold."""
        return (
            self.no_spending_commitments
            and self.no_irreversible_actions
            and self.only_reversible_suggestions
            and bool(self.offer_one_next_action)
            and bool(self.offer_one_question)
        )


@dataclass
class TradeoffResult:
    """Output of the Tradeoff Validator."""
    resolution: TradeoffResolution
    reason: str = ""
    clarifying_question: Optional[str] = None
    safe_action_override: Optional[str] = None
    contradictions: List[str] = None
    safe_minimal_contract: Optional[SafeMinimalContract] = None

    def __post_init__(self):
        if self.contradictions is None:
            self.contradictions = []


# ============================================================================
# CLARIFY vs ESCALATE Boundary
# ============================================================================

# Intents where ONE question gets the missing info → prefer CLARIFY
# These are "scalar-resolvable": budget, deadline, preference, constraint
SCALAR_RESOLVABLE_INTENTS: FrozenSet[str] = frozenset({
    "mobility_booking",         # "What's your budget?"
    "mobility_price_check",     # "Where are you going?"
    "schedule_event",           # "What time works best?"
    "meeting_schedule",         # "What time?"
    "focus_time_block",         # "How long?"
    "deadline_reminder",        # "When is the deadline?"
    "bill_payment",             # "Which bill?"
    "set_savings_goal",         # "What's the target amount?"
    "goal_set",                 # "What's the target amount?"
    "health_goal_set",          # "What's the specific goal?"
    "investment_query",         # "What amount?"
    "loan_inquiry",             # "What amount and term?"
    "travel_booking",           # "What's your budget?"
    "nutrition_log",            # "What did you eat?"
})

# Intents requiring multi-variable reasoning → always ESCALATE
# One question can't resolve these — they need full LLM analysis
MULTI_VARIABLE_INTENTS: FrozenSet[str] = frozenset({
    "career_change",
    "relocation_analysis",
    "tradeoff_analysis",
    "life_event_planning",
    "car_purchase",
})

# Questions to ask per scalar-resolvable intent (targeted, not generic)
_SCALAR_QUESTIONS: dict = {
    "mobility_booking": "What's your budget for this ride?",
    "mobility_price_check": "Where are you heading?",
    "schedule_event": "What time works best for you?",
    "meeting_schedule": "What time should I schedule this?",
    "focus_time_block": "How long do you want to focus — 1 hour, 2 hours?",
    "deadline_reminder": "When is the deadline?",
    "bill_payment": "Which bill would you like to pay?",
    "set_savings_goal": "What's your target savings amount?",
    "goal_set": "What's the target amount for this goal?",
    "health_goal_set": "What specific health target are you aiming for?",
    "investment_query": "How much are you thinking of investing?",
    "loan_inquiry": "What amount and term are you considering?",
    "travel_booking": "What's your budget for this trip?",
    "nutrition_log": "What did you have? I'll log it for you.",
}


# ============================================================================
# Stabilization Steps by Dimension (for SAFE_MINIMAL)
# ============================================================================

_STABILIZATION_STEPS = {
    "wealth": [
        "Review your spending over the past 7 days",
        "Check if any subscriptions can be paused",
        "Set a 24-hour cooling-off period before large purchases",
    ],
    "health": [
        "Take a 5-minute breathing exercise",
        "Go for a short walk",
        "Get at least 7 hours of sleep tonight",
    ],
    "time": [
        "Block 30 minutes of focus time today",
        "Review and cancel one non-essential meeting",
        "Set a 'no-notification' window for deep work",
    ],
}


# ============================================================================
# Thresholds
# ============================================================================

SIGNIFICANT_DELTA = 5.0
SEVERE_DELTA = 15.0
CRISIS_SPEND_THRESHOLD = 8.0


class TradeoffValidator:
    """
    Stage 4.5 of the HELM Intelligence Pipeline (deterministic).

    Validates score deltas for contradictions, risk, and ambiguity.
    Forces appropriate resolution before decision synthesis proceeds.

    Rule priority order:
        1. Crisis-mode spending guardrail → SAFE_MINIMAL
        2. Debt guardrail → SAFE_MINIMAL
        3. Multi-variable intent → ESCALATE (always)
        3.5. Scalar-resolvable intent + low confidence → CLARIFY
        4. Severe opposing deltas + uncertain intent → ESCALATE
        5. Moderate tradeoff + ambiguous intent → CLARIFY
        6. Three-way conflict → ESCALATE
        7. Moderate tradeoff + clear intent → PROCEED (with context)
        8. Default → PROCEED
    """

    def validate(
        self,
        scores: ScoreDeltas,
        intent: IntentResult,
        context: ContextFrame,
    ) -> TradeoffResult:
        """
        Validate tradeoffs in the scored deltas.
        Rules are evaluated in priority order. First matching rule wins.
        """
        contradictions: List[str] = []

        # ------------------------------------------------------------------
        # Rule 1: CRISIS-MODE SPENDING GUARDRAIL → SAFE_MINIMAL
        # ------------------------------------------------------------------
        if context.crisis_mode:
            for dim in context.crisis_dimensions:
                delta = getattr(scores, dim, None)
                if delta and delta.delta < -CRISIS_SPEND_THRESHOLD:
                    logger.info(
                        "Tradeoff: crisis guardrail (%s delta=%.1f) → SAFE_MINIMAL",
                        dim, delta.delta,
                    )
                    contract = self._build_safe_minimal_contract(
                        dimension=dim,
                        reason="crisis_spending",
                        context=context,
                    )
                    return TradeoffResult(
                        resolution=TradeoffResolution.SAFE_MINIMAL,
                        reason=f"User is in {dim} crisis (score < 30) and this action "
                               f"would further decrease {dim} by {abs(delta.delta):.0f} points.",
                        safe_action_override=contract.offer_one_next_action,
                        contradictions=[f"Crisis on {dim} + negative {dim} delta"],
                        safe_minimal_contract=contract,
                    )

        # ------------------------------------------------------------------
        # Rule 2: DEBT GUARDRAIL → SAFE_MINIMAL
        # ------------------------------------------------------------------
        if any("CRITICAL" in gi for gi in scores.goal_impacts):
            contract = self._build_safe_minimal_contract(
                dimension="wealth",
                reason="debt_risk",
                context=context,
            )
            return TradeoffResult(
                resolution=TradeoffResolution.SAFE_MINIMAL,
                reason="Spending exceeds available balance — debt risk detected.",
                safe_action_override=contract.offer_one_next_action,
                contradictions=["Spending exceeds balance"],
                safe_minimal_contract=contract,
            )

        # ------------------------------------------------------------------
        # Rule 3: MULTI-VARIABLE INTENT → ESCALATE (always)
        # One question can't resolve these — needs full LLM analysis.
        # ------------------------------------------------------------------
        if intent.intent in MULTI_VARIABLE_INTENTS:
            logger.info("Tradeoff: multi-variable intent '%s' → ESCALATE", intent.intent)
            return TradeoffResult(
                resolution=TradeoffResolution.ESCALATE,
                reason=f"Intent '{intent.intent}' requires multi-variable reasoning.",
                contradictions=[f"Multi-variable intent: {intent.intent}"],
            )

        # ------------------------------------------------------------------
        # Rule 3.5: SCALAR-RESOLVABLE + LOW CONFIDENCE → CLARIFY
        # The missing piece is one scalar — ask for it instead of escalating.
        # ------------------------------------------------------------------
        if (
            intent.intent in SCALAR_RESOLVABLE_INTENTS
            and intent.confidence < 0.85
        ):
            question = _SCALAR_QUESTIONS.get(
                intent.intent,
                "Could you give me a bit more detail so I can help you better?"
            )
            logger.info("Tradeoff: scalar-resolvable '%s' + conf=%.2f → CLARIFY", intent.intent, intent.confidence)
            return TradeoffResult(
                resolution=TradeoffResolution.CLARIFY,
                reason=f"Missing scalar for '{intent.intent}' — one question can resolve.",
                clarifying_question=question,
                contradictions=[f"Low confidence ({intent.confidence:.2f}) on scalar-resolvable intent"],
            )

        # ------------------------------------------------------------------
        # Rule 4: SEVERE OPPOSING DELTAS + UNCERTAIN INTENT → ESCALATE
        # ------------------------------------------------------------------
        dims = [
            ("wealth", scores.wealth.delta),
            ("health", scores.health.delta),
            ("time", scores.time.delta),
        ]
        for i, (d1_name, d1_val) in enumerate(dims):
            for d2_name, d2_val in dims[i + 1:]:
                if (
                    abs(d1_val) >= SEVERE_DELTA
                    and abs(d2_val) >= SIGNIFICANT_DELTA
                    and (d1_val > 0) != (d2_val > 0)
                ):
                    contradictions.append(
                        f"Severe tradeoff: {d1_name}={d1_val:+.0f} vs {d2_name}={d2_val:+.0f}"
                    )

        if contradictions and intent.confidence < 0.85:
            logger.info("Tradeoff: severe + low confidence → ESCALATE")
            return TradeoffResult(
                resolution=TradeoffResolution.ESCALATE,
                reason="Severe cross-dimensional tradeoff with uncertain intent.",
                contradictions=contradictions,
            )

        # ------------------------------------------------------------------
        # Rule 5: MODERATE TRADEOFF + AMBIGUOUS INTENT → CLARIFY
        # ------------------------------------------------------------------
        if scores.has_tradeoff and intent.confidence < 0.7:
            question = self._generate_clarifying_question(scores, intent)
            logger.info("Tradeoff: moderate + ambiguous → CLARIFY")
            return TradeoffResult(
                resolution=TradeoffResolution.CLARIFY,
                reason="Moderate tradeoff with ambiguous intent — asking for preference.",
                clarifying_question=question,
                contradictions=[
                    f"Tradeoff: {d}={v:+.0f}" for d, v in dims if v != 0
                ],
            )

        # ------------------------------------------------------------------
        # Rule 6: THREE-WAY CONFLICT → ESCALATE
        # ------------------------------------------------------------------
        significant_dims = [(d, v) for d, v in dims if abs(v) >= SIGNIFICANT_DELTA]
        if len(significant_dims) >= 3:
            signs = set(1 if v > 0 else -1 for _, v in significant_dims)
            if len(signs) > 1:
                logger.info("Tradeoff: three-way conflict → ESCALATE")
                return TradeoffResult(
                    resolution=TradeoffResolution.ESCALATE,
                    reason="All three dimensions have significant conflicting impacts.",
                    contradictions=[
                        f"Three-way conflict: {', '.join(f'{d}={v:+.0f}' for d, v in significant_dims)}"
                    ],
                )

        # ------------------------------------------------------------------
        # Rule 7: MODERATE TRADEOFF + CLEAR INTENT → PROCEED with context
        # ------------------------------------------------------------------
        if scores.has_tradeoff and contradictions:
            logger.info(
                "Tradeoff: moderate, clear intent (conf=%.2f) → PROCEED with context",
                intent.confidence,
            )
            return TradeoffResult(
                resolution=TradeoffResolution.PROCEED,
                reason="Moderate tradeoff with clear intent — proceeding with context.",
                contradictions=contradictions,
            )

        # ------------------------------------------------------------------
        # DEFAULT: No contradictions → PROCEED
        # ------------------------------------------------------------------
        return TradeoffResult(
            resolution=TradeoffResolution.PROCEED,
            reason="No significant contradictions detected.",
        )

    # ------------------------------------------------------------------
    # SAFE_MINIMAL Contract Builder
    # ------------------------------------------------------------------

    def _build_safe_minimal_contract(
        self,
        dimension: str,
        reason: str,
        context: ContextFrame,
    ) -> SafeMinimalContract:
        """
        Build a compliance-ready SafeMinimalContract.

        Every contract guarantees:
            - No spending commitments
            - No irreversible actions
            - Exactly 1 next action + 1 question
            - Dimension-specific stabilization steps
        """
        # Dimension-specific next actions
        next_actions = {
            "wealth": (
                "I'd recommend holding off on this for now. Let me show you "
                "your budget overview so we can find a safer path forward."
            ),
            "health": (
                "Let's take a step back and focus on what your body needs right now. "
                "I can suggest a gentle recovery plan."
            ),
            "time": (
                "You've got a lot on your plate. Let me help you prioritize "
                "what's most important today."
            ),
        }

        # Dimension-specific questions
        questions = {
            "wealth": "Would you like me to review your spending this week and find areas where we could save?",
            "health": "Would you like a quick wellness check-in to see where you stand?",
            "time": "Would you like me to audit your schedule and find some breathing room?",
        }

        # Build stabilization steps for the crisis dimension
        steps = _STABILIZATION_STEPS.get(dimension, [])

        return SafeMinimalContract(
            no_spending_commitments=True,
            no_irreversible_actions=True,
            only_reversible_suggestions=True,
            offer_one_next_action=next_actions.get(dimension, next_actions["wealth"]),
            offer_one_question=questions.get(dimension, questions["wealth"]),
            stabilization_steps=steps,
        )

    # ------------------------------------------------------------------
    # Clarifying Question Generator
    # ------------------------------------------------------------------

    def _generate_clarifying_question(
        self, scores: ScoreDeltas, intent: IntentResult
    ) -> str:
        """Generate a deterministic clarifying question based on the tradeoff."""
        pos_dims = []
        neg_dims = []

        for dim_name, delta in [
            ("financial wellbeing", scores.wealth.delta),
            ("health", scores.health.delta),
            ("time", scores.time.delta),
        ]:
            if delta > SIGNIFICANT_DELTA:
                pos_dims.append(dim_name)
            elif delta < -SIGNIFICANT_DELTA:
                neg_dims.append(dim_name)

        if pos_dims and neg_dims:
            pos_str = " and ".join(pos_dims)
            neg_str = " and ".join(neg_dims)
            return (
                f"This would improve your {pos_str} but could impact your {neg_str}. "
                f"Would you like me to prioritize {pos_str}, or find a more balanced option?"
            )

        return (
            "I see a trade-off here. Could you tell me what matters most to you right now "
            "— your finances, health, or time?"
        )
