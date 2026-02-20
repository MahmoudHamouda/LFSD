"""
Stage 4: Score Evaluation Engine — Fully Deterministic, No LLM.

THE HEART OF HELM.

Each intent type maps to a ScoringPolicy — a declarative rule set that specifies:
    - Which dimensions are affected (wealth, health, time)
    - Direction and magnitude of impact
    - Temporal weighting (short-term vs. long-term)
    - Conditional modifiers based on user context

Every score delta traces back to a specific rule and input.

Performance target: < 1ms per evaluation (sub-millisecond).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .schemas import ContextFrame, DimensionDelta, IntentResult, ScoreDeltas

logger = logging.getLogger("intelligence.score_engine")


# ============================================================================
# Scoring Policy Definition
# ============================================================================

@dataclass
class DimensionRule:
    """A single rule for computing a dimension's delta."""
    dimension: str  # "wealth", "health", or "time"
    base_delta: float = 0.0  # Default delta if no modifiers apply
    temporal_weight: str = "short_term"  # "short_term" or "long_term"
    description: str = ""

    # Optional modifier: a callable that takes (IntentResult, ContextFrame)
    # and returns an adjusted delta. If None, base_delta is used.
    modifier: Optional[Callable] = field(default=None, repr=False)


@dataclass
class ScoringPolicy:
    """
    Declarative rule set for computing tri-dimensional impact.
    Versioned, governed, and hot-reloadable.

    Governance fields:
        owner:          Team/person responsible for this policy.
        deprecated:     If True, policy should not be used for new intents.
        superseded_by:  Name of the replacement policy (if deprecated).
        created_at:     ISO date of policy creation.
        changelog:      List of changes per version bump.
    """
    name: str
    version: str = "1.0"
    rules: List[DimensionRule] = field(default_factory=list)
    description: str = ""

    # Governance
    owner: str = "platform"
    deprecated: bool = False
    superseded_by: Optional[str] = None
    created_at: str = "2026-01-01"
    changelog: List[str] = field(default_factory=list)


# ============================================================================
# Policy Modifiers (Context-Aware Delta Adjusters)
# ============================================================================

def _spending_wealth_modifier(intent: IntentResult, ctx: ContextFrame) -> float:
    """Adjust wealth delta based on spending amount vs. income."""
    amount = intent.entities.get("amount", 0)
    if amount <= 0:
        return -1.0  # Minor negative for unquantified spending query

    monthly_income = ctx.financial.monthly_income
    if monthly_income <= 0:
        return -3.0  # No income data — conservative penalty

    ratio = amount / monthly_income
    if ratio > 0.5:
        return -15.0  # Spending > 50% of monthly income
    elif ratio > 0.2:
        return -8.0
    elif ratio > 0.1:
        return -4.0
    else:
        return -2.0


def _goal_set_wealth_modifier(intent: IntentResult, ctx: ContextFrame) -> float:
    """Positive wealth impact for setting savings goals."""
    target = intent.entities.get("target_amount", 0)
    if target > 0:
        return +5.0  # Committing to saving is always positive
    return +2.0


def _car_purchase_wealth_modifier(intent: IntentResult, ctx: ContextFrame) -> float:
    """Car purchase has significant wealth impact."""
    balance = ctx.financial.total_balance
    income = ctx.financial.monthly_income
    emergency = ctx.financial.emergency_fund_months

    if emergency < 3:
        return -20.0  # Insufficient emergency fund
    elif income > 0 and balance / max(income, 1) < 6:
        return -12.0  # Less than 6 months savings
    else:
        return -5.0  # Affordable range


def _car_purchase_time_modifier(intent: IntentResult, ctx: ContextFrame) -> float:
    """Owning a car typically saves commute time."""
    commute = ctx.time.commute_minutes
    if commute > 60:
        return +8.0  # Long commuter benefits most
    elif commute > 30:
        return +4.0
    return +1.0


def _career_change_wealth_modifier(intent: IntentResult, ctx: ContextFrame) -> float:
    """Career change: assess income delta."""
    # Look for percentage or amount in entities
    income_change = intent.entities.get("income_change_pct", 0)
    if income_change > 0:
        return min(+20.0, income_change * 0.5)
    return +5.0  # Default positive assumption


def _career_change_time_modifier(intent: IntentResult, ctx: ContextFrame) -> float:
    """Career change: assess commute and work-life balance impact."""
    commute_change = intent.entities.get("commute_change_minutes", 0)
    if commute_change > 60:
        return -15.0  # Significant commute increase
    elif commute_change > 30:
        return -8.0
    elif commute_change < -30:
        return +8.0  # Commute improvement
    return -3.0  # Default slight negative (transition stress)


def _career_change_health_modifier(intent: IntentResult, ctx: ContextFrame) -> float:
    """Career change: stress from commute and transition."""
    commute_change = intent.entities.get("commute_change_minutes", 0)
    stress_baseline = ctx.health.stress_level
    if commute_change > 60 and stress_baseline > 60:
        return -12.0  # Already stressed + long commute
    elif commute_change > 30:
        return -5.0
    return -2.0  # Transition stress


def _schedule_time_modifier(intent: IntentResult, ctx: ContextFrame) -> float:
    """Scheduling improves time management."""
    wlb = ctx.time.work_life_balance
    if wlb < 40:
        return +5.0  # Poor work-life balance benefits most from scheduling
    return +2.0


def _exercise_health_modifier(intent: IntentResult, ctx: ContextFrame) -> float:
    """Exercise positively impacts health."""
    activity = ctx.health.activity_level
    if activity < 30:
        return +8.0  # Sedentary users benefit most
    elif activity < 60:
        return +5.0
    return +3.0


def _sleep_health_modifier(intent: IntentResult, ctx: ContextFrame) -> float:
    """Sleep analysis awareness improves health behaviors."""
    sleep_quality = ctx.health.sleep_quality
    if sleep_quality < 40:
        return +5.0  # Low sleep quality — awareness is valuable
    return +2.0


def _commute_time_modifier(intent: IntentResult, ctx: ContextFrame) -> float:
    """Commute planning — impact depends on current commute length."""
    commute = ctx.time.commute_minutes
    if commute > 60:
        return +5.0  # Long commuters benefit most
    elif commute > 30:
        return +3.0
    return +1.0


def _relocation_wealth_modifier(intent: IntentResult, ctx: ContextFrame) -> float:
    """Relocation cost-of-living delta."""
    col_change_pct = intent.entities.get("cost_of_living_change_pct", 0)
    if col_change_pct > 20:
        return -12.0  # Significantly more expensive
    elif col_change_pct > 0:
        return -5.0
    elif col_change_pct < -10:
        return +8.0  # Cheaper area
    return 0.0


def _relocation_time_modifier(intent: IntentResult, ctx: ContextFrame) -> float:
    """Relocation — transition uses significant time."""
    current_commute = ctx.time.commute_minutes
    new_commute = intent.entities.get("new_commute_minutes", current_commute)
    delta = new_commute - current_commute
    if delta > 30:
        return -8.0
    elif delta < -20:
        return +5.0
    return -5.0  # General transition time cost


def _subscription_wealth_modifier(intent: IntentResult, ctx: ContextFrame) -> float:
    """Reviewing subscriptions — savings awareness."""
    expenses = ctx.financial.monthly_expenses
    if expenses > ctx.financial.monthly_income * 0.7:
        return +4.0  # High expense ratio — review is very valuable
    return +2.0


def _hydration_health_modifier(intent: IntentResult, ctx: ContextFrame) -> float:
    """Hydration reminder — benefits based on activity level."""
    activity = ctx.health.activity_level
    if activity > 60:
        return +3.0  # Active users benefit more from hydration
    return +2.0


def _deadline_time_modifier(intent: IntentResult, ctx: ContextFrame) -> float:
    """Deadline reminder — accountability improves productivity."""
    productivity = ctx.time.productivity_score
    if productivity < 40:
        return +5.0  # Low productivity benefits most from deadlines
    return +2.0


def _productivity_time_modifier(intent: IntentResult, ctx: ContextFrame) -> float:
    """Reviewing productivity — self-awareness."""
    productivity = ctx.time.productivity_score
    if productivity < 50:
        return +3.0  # Awareness is most valuable when low
    return +1.0


def _budget_wealth_modifier(intent: IntentResult, ctx: ContextFrame) -> float:
    """Budget monitoring — value depends on expense ratio."""
    if ctx.financial.monthly_income > 0:
        ratio = ctx.financial.monthly_expenses / ctx.financial.monthly_income
        if ratio > 0.8:
            return +5.0  # Near-limit spender benefits most
        elif ratio > 0.5:
            return +3.0
    return +1.0


def _salary_wealth_modifier(intent: IntentResult, ctx: ContextFrame) -> float:
    """Salary analysis — awareness of income."""
    income = ctx.financial.monthly_income
    if income > 0:
        return +2.0
    return +1.0  # No income data — still positive to check


def _net_worth_wealth_modifier(intent: IntentResult, ctx: ContextFrame) -> float:
    """Net worth check — asset awareness."""
    balance = ctx.financial.total_balance
    debt = ctx.financial.total_debt
    if debt > balance * 0.5:
        return +4.0  # High debt ratio — awareness is critical
    return +2.0


def _expense_wealth_modifier(intent: IntentResult, ctx: ContextFrame) -> float:
    """Expense categorization — spending pattern awareness."""
    expenses = ctx.financial.monthly_expenses
    income = ctx.financial.monthly_income
    if income > 0 and expenses / income > 0.7:
        return +3.0  # High spender benefits from categorization
    return +1.0


def _life_event_wealth_modifier(intent: IntentResult, ctx: ContextFrame) -> float:
    """Life event — impact depends on financial readiness."""
    emergency = ctx.financial.emergency_fund_months
    if emergency < 3:
        return -15.0  # Insufficient emergency fund
    elif emergency < 6:
        return -8.0
    return -5.0  # Financially prepared


# ============================================================================
# Policy Registry — The Rule Sets
# ============================================================================
# Policy Set Semantic Version
# Bump MAJOR for breaking changes, MINOR for new policies, PATCH for modifier tweaks.
POLICY_SET_VERSION = "2.0.0"

SCORING_POLICIES: Dict[str, ScoringPolicy] = {
    # --- Wealth Policies ---
    "spending_report": ScoringPolicy(
        name="spending_report",
        description="Viewing spending data — awareness is slightly positive for wealth.",
        rules=[
            DimensionRule(dimension="wealth", base_delta=+1.0,
                          description="Awareness of spending patterns"),
        ],
    ),
    "financial_advisory": ScoringPolicy(
        name="financial_advisory",
        description="Seeking financial advice — context-dependent impact.",
        rules=[
            DimensionRule(dimension="wealth", base_delta=-2.0,
                          modifier=_spending_wealth_modifier,
                          description="Depends on amount relative to income"),
        ],
    ),
    "goal_set": ScoringPolicy(
        name="goal_set",
        description="Setting a savings goal — positive for wealth.",
        rules=[
            DimensionRule(dimension="wealth", base_delta=+5.0,
                          modifier=_goal_set_wealth_modifier,
                          description="Commitment to saving is positive"),
        ],
    ),
    "bill_payment": ScoringPolicy(
        name="bill_payment",
        description="Paying bills — responsible financial behavior.",
        rules=[
            DimensionRule(dimension="wealth", base_delta=+2.0,
                          description="Timely bill payment improves financial health"),
            DimensionRule(dimension="time", base_delta=+1.0,
                          description="Automated payment saves time"),
        ],
    ),
    "cashflow_report": ScoringPolicy(
        name="cashflow_report",
        description="Reviewing cashflow — awareness.",
        rules=[
            DimensionRule(dimension="wealth", base_delta=+1.0,
                          description="Cashflow awareness"),
        ],
    ),
    "investment_query": ScoringPolicy(
        name="investment_query",
        description="Investment research — neutral to slightly positive.",
        rules=[
            DimensionRule(dimension="wealth", base_delta=+2.0,
                          description="Investment research is proactive"),
        ],
    ),
    "loan_inquiry": ScoringPolicy(
        name="loan_inquiry",
        description="Loan research — neutral, depends on context.",
        rules=[
            DimensionRule(dimension="wealth", base_delta=-1.0,
                          description="Debt consideration — slight caution"),
        ],
    ),

    # --- Health Policies ---
    "sleep_analysis": ScoringPolicy(
        name="sleep_analysis",
        description="Analyzing sleep — awareness improves behavior.",
        rules=[
            DimensionRule(dimension="health", base_delta=+2.0,
                          modifier=_sleep_health_modifier,
                          description="Sleep awareness"),
        ],
    ),
    "activity_summary": ScoringPolicy(
        name="activity_summary",
        description="Reviewing activity — reinforces healthy behavior.",
        rules=[
            DimensionRule(dimension="health", base_delta=+2.0,
                          modifier=_exercise_health_modifier,
                          description="Activity awareness"),
        ],
    ),
    "nutrition_log": ScoringPolicy(
        name="nutrition_log",
        description="Logging nutrition — awareness and tracking.",
        rules=[
            DimensionRule(dimension="health", base_delta=+3.0,
                          description="Nutrition tracking is proactive"),
        ],
    ),
    "stress_check": ScoringPolicy(
        name="stress_check",
        description="Checking stress levels — self-awareness.",
        rules=[
            DimensionRule(dimension="health", base_delta=+2.0,
                          description="Stress awareness is positive"),
        ],
    ),
    "recovery_status": ScoringPolicy(
        name="recovery_status",
        description="Checking recovery — health awareness.",
        rules=[
            DimensionRule(dimension="health", base_delta=+1.0,
                          description="Recovery monitoring"),
        ],
    ),
    "workout_plan": ScoringPolicy(
        name="workout_plan",
        description="Planning workouts — commitment to fitness.",
        rules=[
            DimensionRule(dimension="health", base_delta=+5.0,
                          modifier=_exercise_health_modifier,
                          description="Workout commitment"),
            DimensionRule(dimension="time", base_delta=-2.0,
                          description="Time investment for exercise"),
        ],
    ),
    "mental_health_check": ScoringPolicy(
        name="mental_health_check",
        description="Mental health check-in — important self-care.",
        rules=[
            DimensionRule(dimension="health", base_delta=+3.0,
                          description="Mental health awareness"),
        ],
    ),
    "health_goal_set": ScoringPolicy(
        name="health_goal_set",
        description="Setting a health goal — commitment.",
        rules=[
            DimensionRule(dimension="health", base_delta=+5.0,
                          description="Health goal commitment"),
        ],
    ),

    # --- Time Policies ---
    "schedule_event": ScoringPolicy(
        name="schedule_event",
        description="Scheduling events — time management.",
        rules=[
            DimensionRule(dimension="time", base_delta=+2.0,
                          modifier=_schedule_time_modifier,
                          description="Proactive scheduling"),
        ],
    ),
    "focus_time_block": ScoringPolicy(
        name="focus_time_block",
        description="Blocking focus time — productivity and health.",
        rules=[
            DimensionRule(dimension="time", base_delta=+5.0,
                          description="Focus time improves productivity"),
            DimensionRule(dimension="health", base_delta=+2.0,
                          description="Focus time reduces stress"),
        ],
    ),
    "meeting_schedule": ScoringPolicy(
        name="meeting_schedule",
        description="Scheduling meetings — neutral time impact.",
        rules=[
            DimensionRule(dimension="time", base_delta=-1.0,
                          description="Meetings consume time"),
        ],
    ),
    "time_audit": ScoringPolicy(
        name="time_audit",
        description="Auditing time usage — awareness.",
        rules=[
            DimensionRule(dimension="time", base_delta=+2.0,
                          description="Time awareness"),
        ],
    ),
    "commute_planning": ScoringPolicy(
        name="commute_planning",
        description="Commute planning — time and cost optimization.",
        rules=[
            DimensionRule(dimension="time", base_delta=+2.0,
                          description="Route optimization"),
            DimensionRule(dimension="wealth", base_delta=+1.0,
                          description="Cost-aware commute"),
        ],
    ),

    # --- Mobility Policies ---
    "mobility_price_check": ScoringPolicy(
        name="mobility_price_check",
        description="Checking ride prices — cost-conscious.",
        rules=[
            DimensionRule(dimension="wealth", base_delta=+1.0,
                          description="Price awareness before spending"),
        ],
    ),
    "mobility_booking": ScoringPolicy(
        name="mobility_booking",
        description="Booking a ride — wealth and time impact.",
        rules=[
            DimensionRule(dimension="wealth", base_delta=-3.0,
                          description="Ride cost"),
            DimensionRule(dimension="time", base_delta=+3.0,
                          description="Time saved vs. alternatives"),
        ],
    ),
    "car_purchase": ScoringPolicy(
        name="car_purchase",
        description="Car purchase — major cross-dimensional decision.",
        rules=[
            DimensionRule(dimension="wealth", base_delta=-10.0,
                          modifier=_car_purchase_wealth_modifier,
                          description="Significant financial commitment"),
            DimensionRule(dimension="time", base_delta=+3.0,
                          modifier=_car_purchase_time_modifier,
                          description="Commute time savings"),
            DimensionRule(dimension="health", base_delta=0.0,
                          description="Neutral health impact"),
        ],
    ),

    # --- Cross-Domain Policies ---
    "tradeoff_analysis": ScoringPolicy(
        name="tradeoff_analysis",
        description="Multi-dimensional tradeoff — computed per scenario.",
        rules=[
            DimensionRule(dimension="wealth", base_delta=0.0,
                          description="Depends on scenario"),
            DimensionRule(dimension="health", base_delta=0.0,
                          description="Depends on scenario"),
            DimensionRule(dimension="time", base_delta=0.0,
                          description="Depends on scenario"),
        ],
    ),
    "career_change": ScoringPolicy(
        name="career_change",
        description="Career change — full tri-dimensional analysis.",
        rules=[
            DimensionRule(dimension="wealth", base_delta=+5.0,
                          modifier=_career_change_wealth_modifier,
                          description="Income change", temporal_weight="long_term"),
            DimensionRule(dimension="time", base_delta=-3.0,
                          modifier=_career_change_time_modifier,
                          description="Commute and schedule change"),
            DimensionRule(dimension="health", base_delta=-2.0,
                          modifier=_career_change_health_modifier,
                          description="Transition stress"),
        ],
    ),
    "relocation_analysis": ScoringPolicy(
        name="relocation_analysis",
        description="Relocation — significant multi-dimensional impact.",
        rules=[
            DimensionRule(dimension="wealth", base_delta=0.0,
                          description="Cost of living delta"),
            DimensionRule(dimension="health", base_delta=0.0,
                          description="Lifestyle change"),
            DimensionRule(dimension="time", base_delta=-5.0,
                          description="Transition time cost"),
        ],
    ),
    "life_event_planning": ScoringPolicy(
        name="life_event_planning",
        description="Major life event — significant cross-dimensional impact.",
        rules=[
            DimensionRule(dimension="wealth", base_delta=-10.0,
                          description="Financial commitment"),
            DimensionRule(dimension="health", base_delta=+2.0,
                          description="Purpose and fulfillment"),
            DimensionRule(dimension="time", base_delta=-5.0,
                          description="Time commitment"),
        ],
    ),

    # --- Phase 2: New Policies ---
    "subscription_review": ScoringPolicy(
        name="subscription_review",
        version="2.0",
        description="Reviewing subscriptions — savings awareness.",
        rules=[
            DimensionRule(dimension="wealth", base_delta=+2.0,
                          modifier=_subscription_wealth_modifier,
                          description="Subscription cost awareness"),
        ],
    ),
    "budget_alert": ScoringPolicy(
        name="budget_alert",
        version="2.0",
        description="Budget monitoring — proactive financial management.",
        rules=[
            DimensionRule(dimension="wealth", base_delta=+1.0,
                          modifier=_budget_wealth_modifier,
                          description="Budget awareness"),
        ],
    ),
    "salary_analysis": ScoringPolicy(
        name="salary_analysis",
        version="2.0",
        description="Salary analysis — income awareness.",
        rules=[
            DimensionRule(dimension="wealth", base_delta=+2.0,
                          modifier=_salary_wealth_modifier,
                          description="Income awareness"),
        ],
    ),
    "net_worth_check": ScoringPolicy(
        name="net_worth_check",
        version="2.0",
        description="Net worth check — asset awareness.",
        rules=[
            DimensionRule(dimension="wealth", base_delta=+2.0,
                          modifier=_net_worth_wealth_modifier,
                          description="Asset and liability awareness"),
        ],
    ),
    "expense_categorize": ScoringPolicy(
        name="expense_categorize",
        version="2.0",
        description="Expense categorization — spending pattern awareness.",
        rules=[
            DimensionRule(dimension="wealth", base_delta=+1.0,
                          modifier=_expense_wealth_modifier,
                          description="Spending pattern management"),
        ],
    ),
    "hydration_reminder": ScoringPolicy(
        name="hydration_reminder",
        version="2.0",
        description="Hydration reminder — basic health habit.",
        rules=[
            DimensionRule(dimension="health", base_delta=+2.0,
                          modifier=_hydration_health_modifier,
                          description="Hydration habit"),
        ],
    ),
    "health_report": ScoringPolicy(
        name="health_report",
        version="2.0",
        description="Health report — comprehensive health awareness.",
        rules=[
            DimensionRule(dimension="health", base_delta=+2.0,
                          description="Health data awareness"),
        ],
    ),
    "deadline_reminder": ScoringPolicy(
        name="deadline_reminder",
        version="2.0",
        description="Deadline reminder — accountability.",
        rules=[
            DimensionRule(dimension="time", base_delta=+2.0,
                          modifier=_deadline_time_modifier,
                          description="Deadline accountability"),
        ],
    ),
    "productivity_report": ScoringPolicy(
        name="productivity_report",
        version="2.0",
        description="Productivity report — time awareness.",
        rules=[
            DimensionRule(dimension="time", base_delta=+1.0,
                          modifier=_productivity_time_modifier,
                          description="Productivity awareness"),
        ],
    ),
    "set_savings_goal": ScoringPolicy(
        name="set_savings_goal",
        version="2.0",
        description="Setting savings goal — commitment to wealth building.",
        rules=[
            DimensionRule(dimension="wealth", base_delta=+5.0,
                          modifier=_goal_set_wealth_modifier,
                          description="Savings commitment"),
        ],
    ),
}


# ============================================================================
# Score Evaluation Engine
# ============================================================================

class ScoreEvaluationEngine:
    """
    Stage 4 of the HELM Intelligence Pipeline.

    Computes tri-dimensional impact scores using deterministic policy rules.
    Sub-millisecond execution. Fully unit-testable. Every delta traces to a rule.
    """

    def evaluate(
        self,
        intent: IntentResult,
        context: ContextFrame,
    ) -> ScoreDeltas:
        """
        Evaluate the tri-dimensional impact of the classified intent
        against the user's current context.

        Args:
            intent: Classified intent from Stage 3.
            context: Assembled context from Stage 2.

        Returns:
            ScoreDeltas with wealth, health, and time impact.
        """
        # Get the scoring policy for this intent
        entry_from_taxonomy = None
        try:
            from .intent_taxonomy import get_intent_entry
            entry_from_taxonomy = get_intent_entry(intent.intent)
        except ImportError:
            pass

        policy_name = ""
        if entry_from_taxonomy and entry_from_taxonomy.scoring_policy:
            policy_name = entry_from_taxonomy.scoring_policy
        else:
            policy_name = intent.intent  # Fall back to intent name as policy name

        policy = SCORING_POLICIES.get(policy_name)

        if policy is None:
            # No scoring policy for this intent — return neutral deltas
            logger.debug("No scoring policy for intent '%s' — neutral deltas", intent.intent)
            return ScoreDeltas(policies_applied=[])

        # Evaluate each rule
        deltas = {"wealth": 0.0, "health": 0.0, "time": 0.0}
        rule_descriptions = {"wealth": "", "health": "", "time": ""}
        rule_names = {"wealth": "", "health": "", "time": ""}
        temporal = {"wealth": "short_term", "health": "short_term", "time": "short_term"}

        for rule in policy.rules:
            dim = rule.dimension
            if dim not in deltas:
                continue

            # Compute delta: use modifier if available, else base_delta
            if rule.modifier is not None:
                try:
                    delta = rule.modifier(intent, context)
                except Exception as e:
                    logger.warning("Modifier failed for %s.%s: %s", policy.name, dim, e)
                    delta = rule.base_delta
            else:
                delta = rule.base_delta

            # Clamp to [-100, +100]
            delta = max(-100.0, min(100.0, delta))

            deltas[dim] += delta
            rule_descriptions[dim] = rule.description
            rule_names[dim] = f"{policy.name}.{dim}"
            temporal[dim] = rule.temporal_weight

        # Apply crisis modifiers
        if context.crisis_mode:
            deltas, goal_impacts_extra = self._apply_crisis_modifiers(
                deltas, context, intent
            )
        else:
            goal_impacts_extra = []

        # Evaluate goal impacts
        goal_impacts = self._evaluate_goal_impacts(intent, context, deltas)
        goal_impacts.extend(goal_impacts_extra)

        # Build ScoreDeltas
        def _direction(d: float) -> str:
            if d > 0: return "up"
            if d < 0: return "down"
            return "neutral"

        # Determine net impact
        total = sum(deltas.values())
        non_zero = [d for d in deltas.values() if d != 0]
        signs = set(1 if d > 0 else -1 for d in non_zero) if non_zero else {0}

        if len(signs) > 1:
            net_impact = "mixed"
            has_tradeoff = True
        elif total > 0:
            net_impact = "positive"
            has_tradeoff = False
        elif total < 0:
            net_impact = "negative"
            has_tradeoff = False
        else:
            net_impact = "neutral"
            has_tradeoff = False

        result = ScoreDeltas(
            wealth=DimensionDelta(
                dimension="wealth",
                delta=deltas["wealth"],
                direction=_direction(deltas["wealth"]),
                policy_rule=rule_names.get("wealth", ""),
                reasoning=rule_descriptions.get("wealth", ""),
                temporal_weight=temporal.get("wealth", "short_term"),
            ),
            health=DimensionDelta(
                dimension="health",
                delta=deltas["health"],
                direction=_direction(deltas["health"]),
                policy_rule=rule_names.get("health", ""),
                reasoning=rule_descriptions.get("health", ""),
                temporal_weight=temporal.get("health", "short_term"),
            ),
            time=DimensionDelta(
                dimension="time",
                delta=deltas["time"],
                direction=_direction(deltas["time"]),
                policy_rule=rule_names.get("time", ""),
                reasoning=rule_descriptions.get("time", ""),
                temporal_weight=temporal.get("time", "short_term"),
            ),
            net_impact=net_impact,
            has_tradeoff=has_tradeoff,
            crisis_override=context.crisis_mode,
            goal_impacts=goal_impacts,
            policies_applied=[policy.name],
        )

        logger.info(
            "Score evaluation: W=%.1f H=%.1f T=%.1f (net=%s, policy=%s)",
            deltas["wealth"], deltas["health"], deltas["time"],
            net_impact, policy.name,
        )

        return result

    # ------------------------------------------------------------------
    # Crisis & Goal Impact Modifiers
    # ------------------------------------------------------------------

    def _apply_crisis_modifiers(
        self,
        deltas: Dict[str, float],
        context: ContextFrame,
        intent: IntentResult,
    ) -> tuple:
        """Apply crisis-mode modifiers when any dimension is below 30."""
        goal_impacts = []

        for dim in context.crisis_dimensions:
            if dim == "health" and deltas.get("health", 0) > 0:
                # In health crisis, amplify positive health gains
                deltas["health"] *= 1.5
                goal_impacts.append(
                    f"CRISIS OVERRIDE: Health priority — amplifying health benefit."
                )
            elif dim == "wealth" and deltas.get("wealth", 0) < -5:
                # In wealth crisis, amplify negative wealth impacts
                deltas["wealth"] *= 1.3
                goal_impacts.append(
                    f"CRISIS WARNING: Financial stress — spending impact amplified."
                )

        return deltas, goal_impacts

    def _evaluate_goal_impacts(
        self,
        intent: IntentResult,
        context: ContextFrame,
        deltas: Dict[str, float],
    ) -> List[str]:
        """Evaluate impact on user's life goals."""
        impacts = []

        if deltas.get("wealth", 0) < -5 and context.life_goals:
            for goal in context.life_goals:
                if goal.get("priority") == "high":
                    impacts.append(
                        f"May delay '{goal.get('title', 'goal')}' progress."
                    )
                    break

        # Hard guardrail: check if spending exceeds total balance
        amount = intent.entities.get("amount", 0)
        if amount > 0 and amount > context.financial.total_balance:
            impacts.append(
                "CRITICAL: This amount exceeds your total balance. Debt risk."
            )

        return impacts


# ============================================================================
# Policy Governance: Registry Validation
# ============================================================================

def validate_policy_registry() -> Dict[str, List[str]]:
    """
    Validate the scoring policy registry for completeness and correctness.

    Returns a dict of issues by category:
        - "missing":    Intents with no scoring policy
        - "orphaned":   Policies not mapped to any intent
        - "deprecated": Deprecated policies still in active use
        - "superseded": Deprecated policies missing 'superseded_by'

    Call this in CI or at startup to catch drift.
    """
    issues: Dict[str, List[str]] = {
        "missing": [],
        "orphaned": [],
        "deprecated": [],
        "superseded": [],
    }

    # Get all intent names from taxonomy
    try:
        from .intent_taxonomy import get_all_intent_names, get_intent_entry
        all_intents = get_all_intent_names()
    except ImportError:
        logger.warning("Cannot validate: intent_taxonomy not importable")
        return issues

    # Check: every intent with a scoring_policy reference has a matching policy
    policy_names_used = set()
    for intent_name in all_intents:
        entry = get_intent_entry(intent_name)
        if entry and entry.scoring_policy:
            policy_names_used.add(entry.scoring_policy)
            if entry.scoring_policy not in SCORING_POLICIES:
                issues["missing"].append(
                    f"Intent '{intent_name}' references policy '{entry.scoring_policy}' "
                    f"but it doesn't exist in SCORING_POLICIES"
                )
        elif intent_name in SCORING_POLICIES:
            # Intent name matches a policy directly
            policy_names_used.add(intent_name)

    # Check: orphaned policies (exist but no intent uses them)
    for policy_name in SCORING_POLICIES:
        if policy_name not in policy_names_used:
            # Also check if any intent has this name directly
            if policy_name not in all_intents:
                issues["orphaned"].append(policy_name)

    # Check: deprecated policies still referenced
    for policy_name, policy in SCORING_POLICIES.items():
        if policy.deprecated and policy_name in policy_names_used:
            issues["deprecated"].append(
                f"Policy '{policy_name}' is deprecated but still referenced by intents"
            )
        if policy.deprecated and not policy.superseded_by:
            issues["superseded"].append(
                f"Policy '{policy_name}' is deprecated but missing 'superseded_by'"
            )

    return issues

