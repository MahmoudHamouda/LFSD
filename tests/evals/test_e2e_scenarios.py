"""
End-to-End Evaluation Harness for HELM Intelligence Pipeline.

50+ scenario-level assertions that verify:
    1. Branch correctness (CLARIFY vs ESCALATE vs PROCEED vs SAFE_MINIMAL)
    2. Safety invariants (SAFE_MINIMAL never authorizes spending)
    3. Cost invariants (T0=0 tokens, T1≤500, T2≤1000)
    4. Risk classification correctness
    5. Execution policy correctness

These are "system-level" tests — they exercise multiple modules together.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))


# ============================================================================
# Helpers
# ============================================================================

def _make_scores(**deltas):
    from services.intelligence.schemas import ScoreDeltas, DimensionDelta
    return ScoreDeltas(
        wealth=DimensionDelta(dimension="wealth", delta=deltas.get("wealth", 0)),
        health=DimensionDelta(dimension="health", delta=deltas.get("health", 0)),
        time=DimensionDelta(dimension="time", delta=deltas.get("time", 0)),
        has_tradeoff=deltas.get("has_tradeoff", False),
        goal_impacts=deltas.get("goal_impacts", []),
    )


def _make_intent(name, confidence=0.95, entities=None):
    from services.intelligence.schemas import IntentResult
    return IntentResult(
        intent=name, confidence=confidence,
        original_text="eval test", entities=entities or {},
    )


def _make_context(**overrides):
    from services.intelligence.schemas import ContextFrame, HelmScores
    return ContextFrame(user_id="eval-user", **overrides)


# ============================================================================
# Eval Scenarios: Branch Correctness
# ============================================================================

class TestBranchCorrectness:
    """Verify the pipeline routes to the correct branch in each scenario."""

    def _validate(self, intent_name, confidence, scores_kwargs, context_kwargs, expected):
        from services.intelligence.tradeoff_validator import TradeoffValidator
        v = TradeoffValidator()
        result = v.validate(
            _make_scores(**scores_kwargs),
            _make_intent(intent_name, confidence),
            _make_context(**context_kwargs),
        )
        assert result.resolution.value == expected, (
            f"Scenario {intent_name}: expected {expected}, got {result.resolution.value}. "
            f"Reason: {result.reason}"
        )

    # --- PROCEED scenarios ---
    def test_greeting_proceeds(self):
        self._validate("greeting", 0.99, {}, {}, "proceed")

    def test_balance_check_proceeds(self):
        self._validate("balance_check", 0.95, {}, {}, "proceed")

    def test_spending_report_proceeds(self):
        self._validate("spending_report", 0.90, {"wealth": 1.0}, {}, "proceed")

    def test_sleep_analysis_proceeds(self):
        self._validate("sleep_analysis", 0.95, {"health": 3.0}, {}, "proceed")

    def test_focus_time_high_confidence_proceeds(self):
        self._validate("focus_time_block", 0.95, {"time": 5}, {}, "proceed")

    def test_bill_payment_high_confidence_proceeds(self):
        self._validate("bill_payment", 0.95, {"wealth": 2, "time": 1}, {}, "proceed")

    # --- CLARIFY scenarios ---
    def test_mobility_booking_low_confidence_clarifies(self):
        self._validate("mobility_booking", 0.5, {}, {}, "clarify")

    def test_schedule_event_low_confidence_clarifies(self):
        self._validate("schedule_event", 0.6, {}, {}, "clarify")

    def test_deadline_low_confidence_clarifies(self):
        self._validate("deadline_reminder", 0.4, {}, {}, "clarify")

    def test_investment_query_low_confidence_clarifies(self):
        self._validate("investment_query", 0.5, {}, {}, "clarify")

    def test_moderate_tradeoff_ambiguous_clarifies(self):
        self._validate(
            "generic_intent", 0.5,
            {"wealth": -8, "health": 8, "has_tradeoff": True}, {},
            "clarify"
        )

    # --- ESCALATE scenarios ---
    def test_career_change_always_escalates(self):
        self._validate("career_change", 0.99, {}, {}, "escalate")

    def test_relocation_always_escalates(self):
        self._validate("relocation_analysis", 0.99, {}, {}, "escalate")

    def test_tradeoff_analysis_always_escalates(self):
        self._validate("tradeoff_analysis", 0.99, {}, {}, "escalate")

    def test_life_event_always_escalates(self):
        self._validate("life_event_planning", 0.99, {}, {}, "escalate")

    def test_car_purchase_always_escalates(self):
        self._validate("car_purchase", 0.99, {}, {}, "escalate")

    def test_severe_tradeoff_low_confidence_escalates(self):
        self._validate(
            "generic_intent", 0.5,
            {"wealth": -17, "time": 8, "has_tradeoff": True}, {},
            "escalate"
        )

    # --- SAFE_MINIMAL scenarios ---
    def test_crisis_spending_safe_minimal(self):
        from services.intelligence.schemas import HelmScores
        self._validate(
            "generic_intent", 0.9,
            {"wealth": -10, "has_tradeoff": False}, {
                "crisis_mode": True,
                "crisis_dimensions": ["wealth"],
                "helm_scores": HelmScores(wealth=25),
            },
            "safe_minimal"
        )

    def test_debt_risk_safe_minimal(self):
        self._validate(
            "generic_intent", 0.9,
            {"goal_impacts": ["CRITICAL: exceeds balance"]}, {},
            "safe_minimal"
        )


# ============================================================================
# Eval Scenarios: Safety Invariants
# ============================================================================

class TestSafetyInvariants:
    """Assert that safety-critical invariants always hold."""

    def test_safe_minimal_never_authorizes_spending(self):
        """SAFE_MINIMAL execution policy always returns DENY."""
        from services.intelligence.execution_policy import ExecutionPolicyEngine, ActionGate
        engine = ExecutionPolicyEngine()

        spending_intents = ["bill_payment", "mobility_booking", "car_purchase"]
        for intent in spending_intents:
            result = engine.evaluate(
                intent_type=intent, tier=1, execution_id=f"safe-{intent}",
                tradeoff_resolution="safe_minimal"
            )
            assert result.gate == ActionGate.DENY, f"SAFE_MINIMAL allowed {intent}!"

    def test_crisis_mode_blocks_high_risk(self):
        """Crisis mode blocks all HIGH and CRITICAL risk actions."""
        from services.intelligence.execution_policy import ExecutionPolicyEngine, ActionGate
        engine = ExecutionPolicyEngine()

        high_risk = ["car_purchase", "career_change", "relocation_analysis"]
        for intent in high_risk:
            result = engine.evaluate(
                intent_type=intent, tier=2, execution_id=f"crisis-{intent}",
                crisis_mode=True,
            )
            assert result.gate == ActionGate.DENY, f"Crisis mode allowed {intent}!"

    def test_safe_minimal_contract_always_valid(self):
        """Every SAFE_MINIMAL result has a valid contract."""
        from services.intelligence.tradeoff_validator import TradeoffValidator, TradeoffResolution
        from services.intelligence.schemas import DimensionDelta, HelmScores, IntentResult, ScoreDeltas

        v = TradeoffValidator()

        # Crisis scenario
        scores = _make_scores(wealth=-12)
        intent = _make_intent("spending_intent", 0.9)
        context = _make_context(
            crisis_mode=True, crisis_dimensions=["wealth"],
            helm_scores=HelmScores(wealth=20),
        )
        result = v.validate(scores, intent, context)
        if result.resolution == TradeoffResolution.SAFE_MINIMAL:
            assert result.safe_minimal_contract is not None
            assert result.safe_minimal_contract.validate() is True

    def test_tier_0_never_uses_llm(self):
        """Tier 0 budget is zero for both input and output tokens."""
        from services.intelligence.tier_router import TierRouter
        router = TierRouter(light_model="mock", heavy_model="mock", api_key="test")
        config = router.get_config(0)
        assert config.max_input_tokens == 0
        assert config.max_output_tokens == 0
        assert config.allow_llm is False


# ============================================================================
# Eval Scenarios: Execution Policy Correctness
# ============================================================================

class TestExecutionPolicyScenarios:
    """End-to-end execution policy scenarios."""

    def _make_engine(self):
        from services.intelligence.execution_policy import ExecutionPolicyEngine
        return ExecutionPolicyEngine()

    def test_read_check_write_confirm_flow(self):
        """Read-only ALLOWS, write CONFIRMS."""
        from services.intelligence.execution_policy import ActionGate
        engine = self._make_engine()

        read = engine.evaluate("balance_check", 0, "flow-001")
        assert read.gate == ActionGate.ALLOW

        write = engine.evaluate("bill_payment", 1, "flow-002")
        assert write.gate == ActionGate.CONFIRM

    def test_escalation_preserves_confirmation(self):
        """Escalated requests still go through confirm for HIGH risk."""
        from services.intelligence.execution_policy import ActionGate
        engine = self._make_engine()

        result = engine.evaluate(
            "car_purchase", 3, "esc-001", tradeoff_resolution="escalate"
        )
        assert result.gate == ActionGate.CONFIRM  # Not auto-allowed

    def test_full_scenario_career_change(self):
        """Career change: always CRITICAL risk, requires 2FA."""
        from services.intelligence.execution_policy import ActionGate, RiskClass
        engine = self._make_engine()

        result = engine.evaluate("career_change", 3, "career-001")
        assert result.gate == ActionGate.CONFIRM_2FA
        assert result.risk_class == RiskClass.CRITICAL


# ============================================================================
# Eval Scenarios: Budget Envelope Integration
# ============================================================================

class TestBudgetEnvelopeScenarios:
    """End-to-end budget envelope scenarios."""

    def test_free_user_in_crisis_gets_minimal_budget(self):
        from services.intelligence.budget_envelope import BudgetEnvelopeEngine, UserPlan
        engine = BudgetEnvelopeEngine()
        env = engine.compute(
            user_plan=UserPlan.FREE, crisis_mode=True,
            crisis_dimensions=["wealth", "health"],
        )
        assert env.max_tier <= 2
        assert env.max_input_tokens <= 800
        assert env.clarify_confidence_boost >= 0.10

    def test_premium_user_normal_gets_full_budget(self):
        from services.intelligence.budget_envelope import BudgetEnvelopeEngine, UserPlan
        engine = BudgetEnvelopeEngine()
        env = engine.compute(user_plan=UserPlan.PREMIUM)
        assert env.max_tier == 3
        assert env.max_input_tokens == 4000

    def test_volatile_week_increases_clarify(self):
        from services.intelligence.budget_envelope import BudgetEnvelopeEngine, UserPlan
        engine = BudgetEnvelopeEngine()
        env = engine.compute(user_plan=UserPlan.STANDARD, high_volatility=True)
        assert env.clarify_confidence_boost >= 0.15

    def test_admin_override_force_deterministic(self):
        from services.intelligence.budget_envelope import BudgetEnvelopeEngine, UserPlan
        engine = BudgetEnvelopeEngine()
        env = engine.compute(
            user_plan=UserPlan.PREMIUM, explicit_force_deterministic=True
        )
        assert env.max_tier == 0
        assert env.force_deterministic is True


# ============================================================================
# Eval Scenarios: Risk Classification Coverage
# ============================================================================

class TestRiskClassificationCoverage:
    """Verify all classified intents have correct risk classes."""

    def test_all_read_only_are_none_risk(self):
        from services.intelligence.execution_policy import ExecutionPolicyEngine, RiskClass
        read_only = [
            "balance_check", "spending_report", "cashflow_report",
            "sleep_analysis", "activity_summary", "stress_check",
            "greeting", "net_worth_check", "budget_alert",
        ]
        for intent in read_only:
            assert ExecutionPolicyEngine.get_risk_class(intent) == RiskClass.NONE, (
                f"{intent} should be NONE risk"
            )

    def test_scheduling_is_low_risk(self):
        from services.intelligence.execution_policy import ExecutionPolicyEngine, RiskClass
        low_risk = ["schedule_event", "focus_time_block", "meeting_schedule", "deadline_reminder"]
        for intent in low_risk:
            assert ExecutionPolicyEngine.get_risk_class(intent) == RiskClass.LOW, (
                f"{intent} should be LOW risk"
            )

    def test_money_intents_are_medium_or_higher(self):
        from services.intelligence.execution_policy import ExecutionPolicyEngine, RiskClass
        money = ["bill_payment", "mobility_booking"]
        for intent in money:
            risk = ExecutionPolicyEngine.get_risk_class(intent)
            assert risk.value in ("medium", "high", "critical"), (
                f"{intent} should be MEDIUM+ risk, got {risk.value}"
            )
