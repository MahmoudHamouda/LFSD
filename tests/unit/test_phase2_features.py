"""
Phase 2 Unit Tests for HELM Intelligence Pipeline.

Tests: Tier Router, Pipeline Cache, Cost Tracker, Tradeoff Validator,
       Golden Scoring Cases, new scoring policies, enriched templates,
       and DecisionRecord schema.
"""

import sys
import os
import json
import time
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))


# ============================================================================
# Tier Router Tests
# ============================================================================

class TestTierRouter:
    """Tests for the Tier Router (model factory + budget enforcement)."""

    def _make_router(self, api_key="test-key"):
        from services.intelligence.tier_router import TierRouter
        return TierRouter(
            light_model="mock_light",
            heavy_model="mock_heavy",
            api_key=api_key,
        )

    def test_tier_0_no_model(self):
        """Tier 0 returns no model (fully deterministic)."""
        router = self._make_router()
        assert router.get_model_for_tier(0) is None

    def test_tier_1_light_model(self):
        router = self._make_router()
        assert router.get_model_for_tier(1) == "mock_light"

    def test_tier_2_light_model(self):
        router = self._make_router()
        assert router.get_model_for_tier(2) == "mock_light"

    def test_tier_3_heavy_model(self):
        router = self._make_router()
        assert router.get_model_for_tier(3) == "mock_heavy"

    def test_mock_mode_returns_none(self):
        """In mock mode, all tiers return None."""
        router = self._make_router(api_key="mock")
        assert router.get_model_for_tier(1) is None
        assert router.get_model_for_tier(3) is None

    def test_budget_check(self):
        router = self._make_router()
        # Tier 1 budget: 400 input, 100 output
        assert router.is_within_budget(1, 300, 80) is True
        assert router.is_within_budget(1, 500, 80) is False
        assert router.is_within_budget(1, 300, 150) is False

    def test_cost_estimation(self):
        router = self._make_router()
        cost = router.estimate_cost(1, 1000, 500)
        assert cost > 0
        assert isinstance(cost, float)

    def test_cost_tier_3_higher_than_tier_1(self):
        router = self._make_router()
        cost_1 = router.estimate_cost(1, 1000, 500)
        cost_3 = router.estimate_cost(3, 1000, 500)
        assert cost_3 > cost_1

    def test_get_config(self):
        from services.intelligence.tier_router import TierConfig
        router = self._make_router()
        config = router.get_config(2)
        assert config.max_input_tokens == 800
        assert config.allow_llm is True


# ============================================================================
# Pipeline Cache Tests
# ============================================================================

class TestPipelineCache:
    """Tests for PipelineCache (in-memory backend)."""

    def _make_cache(self):
        from services.intelligence.cache import PipelineCache
        return PipelineCache(redis_url=None)  # Force in-memory

    def _make_model(self):
        from services.intelligence.schemas import ContextFrame
        return ContextFrame(user_id="test-user", user_name="Test")

    def test_set_and_get(self):
        from services.intelligence.schemas import ContextFrame
        cache = self._make_cache()
        model = self._make_model()
        cache.set("ctx", "user1", model)
        result = cache.get("ctx", "user1", ContextFrame)
        assert result is not None
        assert result.user_name == "Test"

    def test_cache_miss(self):
        from services.intelligence.schemas import ContextFrame
        cache = self._make_cache()
        result = cache.get("ctx", "nonexistent", ContextFrame)
        assert result is None

    def test_invalidate(self):
        from services.intelligence.schemas import ContextFrame
        cache = self._make_cache()
        model = self._make_model()
        cache.set("ctx", "user1", model)
        cache.invalidate("ctx", "user1")
        result = cache.get("ctx", "user1", ContextFrame)
        assert result is None

    def test_invalidate_user(self):
        from services.intelligence.schemas import ContextFrame
        cache = self._make_cache()
        model = self._make_model()
        cache.set("ctx", "user1", model)
        cache.invalidate_user("user1")
        result = cache.get("ctx", "user1", ContextFrame)
        assert result is None

    def test_namespace_isolation(self):
        """Different namespaces don't collide."""
        from services.intelligence.schemas import ContextFrame
        cache = self._make_cache()
        model = self._make_model()
        cache.set("ctx", "key1", model)
        result = cache.get("intent", "key1", ContextFrame)
        assert result is None  # Different namespace

    def test_backend_reports_memory(self):
        cache = self._make_cache()
        assert cache.backend == "memory"

    def test_stats(self):
        cache = self._make_cache()
        stats = cache.stats()
        assert stats["backend"] == "memory"
        assert "entries" in stats

    def test_hash_key_deterministic(self):
        from services.intelligence.cache import PipelineCache
        h1 = PipelineCache.hash_key("a", "b", "c")
        h2 = PipelineCache.hash_key("a", "b", "c")
        assert h1 == h2

    def test_hash_key_unique(self):
        from services.intelligence.cache import PipelineCache
        h1 = PipelineCache.hash_key("a", "b")
        h2 = PipelineCache.hash_key("a", "c")
        assert h1 != h2


# ============================================================================
# Cost Tracker Tests
# ============================================================================

class TestCostTracker:
    """Tests for CostTracker (per-request budget enforcement)."""

    def _make_tracker(self, tier=1):
        from services.intelligence.cost_tracker import CostTracker
        from services.intelligence.tier_router import TierRouter
        router = TierRouter(light_model=None, heavy_model=None, api_key="test")
        return CostTracker(tier=tier, tier_router=router)

    def test_empty_summary(self):
        tracker = self._make_tracker()
        summary = tracker.summarize()
        assert summary.total_tokens == 0
        assert summary.estimated_cost_usd == 0.0
        assert summary.budget_exceeded is False

    def test_record_usage(self):
        tracker = self._make_tracker()
        tracker.record_usage("intent", input_tokens=200, output_tokens=50)
        summary = tracker.summarize()
        assert summary.total_input_tokens == 200
        assert summary.total_output_tokens == 50
        assert summary.total_tokens == 250

    def test_accumulation(self):
        tracker = self._make_tracker()
        tracker.record_usage("intent", input_tokens=200, output_tokens=50)
        tracker.record_usage("response", input_tokens=100, output_tokens=80)
        summary = tracker.summarize()
        assert summary.total_input_tokens == 300
        assert summary.total_output_tokens == 130
        assert len(summary.stages) == 2

    def test_can_spend_within_budget(self):
        tracker = self._make_tracker(tier=1)
        # Tier 1: max 400 input, 100 output
        assert tracker.can_spend(300, 80) is True

    def test_can_spend_exceeds_budget(self):
        tracker = self._make_tracker(tier=1)
        tracker.record_usage("intent", input_tokens=300, output_tokens=50)
        assert tracker.can_spend(200, 50) is False  # Would exceed input budget

    def test_tier_0_cannot_spend(self):
        tracker = self._make_tracker(tier=0)
        assert tracker.can_spend(1, 0) is False

    def test_budget_exceeded_flag(self):
        tracker = self._make_tracker(tier=1)
        tracker.record_usage("intent", input_tokens=500, output_tokens=50)
        summary = tracker.summarize()
        assert summary.budget_exceeded is True

    def test_cost_positive_for_nonzero_tokens(self):
        tracker = self._make_tracker(tier=1)
        tracker.record_usage("intent", input_tokens=100, output_tokens=50)
        summary = tracker.summarize()
        assert summary.estimated_cost_usd > 0

    def test_to_dict(self):
        tracker = self._make_tracker()
        summary = tracker.summarize()
        d = summary.to_dict()
        assert "tier" in d
        assert "total_tokens" in d


# ============================================================================
# Tradeoff Validator Tests
# ============================================================================

class TestTradeoffValidator:
    """Tests for the deterministic Tradeoff Validator."""

    def _make_validator(self):
        from services.intelligence.tradeoff_validator import TradeoffValidator
        return TradeoffValidator()

    def _make_scores(self, **kwargs):
        from services.intelligence.schemas import ScoreDeltas, DimensionDelta
        defaults = {
            "wealth": DimensionDelta(dimension="wealth"),
            "health": DimensionDelta(dimension="health"),
            "time": DimensionDelta(dimension="time"),
        }
        defaults.update(kwargs)
        return ScoreDeltas(**defaults)

    def _make_intent(self, intent_name="test", confidence=0.95):
        from services.intelligence.schemas import IntentResult
        return IntentResult(intent=intent_name, confidence=confidence, original_text="test")

    def _make_context(self, **overrides):
        from services.intelligence.schemas import ContextFrame, HelmScores
        return ContextFrame(user_id="test", **overrides)

    def test_no_contradictions_proceed(self):
        """No significant deltas → PROCEED."""
        from services.intelligence.tradeoff_validator import TradeoffResolution
        v = self._make_validator()
        result = v.validate(self._make_scores(), self._make_intent(), self._make_context())
        assert result.resolution == TradeoffResolution.PROCEED

    def test_crisis_mode_spending_guardrail(self):
        """Crisis mode + negative delta on crisis dimension → SAFE_MINIMAL."""
        from services.intelligence.tradeoff_validator import TradeoffResolution
        from services.intelligence.schemas import DimensionDelta, HelmScores

        v = self._make_validator()
        scores = self._make_scores(
            wealth=DimensionDelta(dimension="wealth", delta=-10.0),
        )
        context = self._make_context(
            crisis_mode=True,
            crisis_dimensions=["wealth"],
            helm_scores=HelmScores(wealth=25, health=60, time=50),
        )
        result = v.validate(scores, self._make_intent(), context)
        assert result.resolution == TradeoffResolution.SAFE_MINIMAL
        assert "crisis" in result.reason.lower()
        assert result.safe_action_override is not None

    def test_debt_guardrail(self):
        """CRITICAL goal impact → SAFE_MINIMAL."""
        from services.intelligence.tradeoff_validator import TradeoffResolution

        v = self._make_validator()
        scores = self._make_scores()
        scores.goal_impacts = ["CRITICAL: This exceeds balance"]
        result = v.validate(scores, self._make_intent(), self._make_context())
        assert result.resolution == TradeoffResolution.SAFE_MINIMAL

    def test_severe_opposing_deltas_escalation(self):
        """Severe opposing deltas + low confidence → ESCALATE."""
        from services.intelligence.tradeoff_validator import TradeoffResolution
        from services.intelligence.schemas import DimensionDelta

        v = self._make_validator()
        scores = self._make_scores(
            wealth=DimensionDelta(dimension="wealth", delta=-20.0),
            time=DimensionDelta(dimension="time", delta=+10.0),
            has_tradeoff=True,
        )
        intent = self._make_intent(confidence=0.7)
        result = v.validate(scores, intent, self._make_context())
        assert result.resolution == TradeoffResolution.ESCALATE
        assert len(result.contradictions) > 0

    def test_moderate_tradeoff_ambiguous_intent_clarify(self):
        """Moderate tradeoff + low confidence → CLARIFY."""
        from services.intelligence.tradeoff_validator import TradeoffResolution
        from services.intelligence.schemas import DimensionDelta

        v = self._make_validator()
        scores = self._make_scores(
            wealth=DimensionDelta(dimension="wealth", delta=-3.0),
            health=DimensionDelta(dimension="health", delta=+3.0),
            has_tradeoff=True,
        )
        intent = self._make_intent(confidence=0.5)
        result = v.validate(scores, intent, self._make_context())
        assert result.resolution == TradeoffResolution.CLARIFY
        assert result.clarifying_question is not None

    def test_moderate_tradeoff_clear_intent_proceed(self):
        """Moderate tradeoff + high confidence → PROCEED."""
        from services.intelligence.tradeoff_validator import TradeoffResolution
        from services.intelligence.schemas import DimensionDelta

        v = self._make_validator()
        scores = self._make_scores(
            wealth=DimensionDelta(dimension="wealth", delta=-3.0),
            time=DimensionDelta(dimension="time", delta=+3.0),
            has_tradeoff=True,
        )
        # Note: no significant deltas >= SIGNIFICANT_DELTA(5), so no contradictions
        intent = self._make_intent(confidence=0.95)
        result = v.validate(scores, intent, self._make_context())
        assert result.resolution == TradeoffResolution.PROCEED

    def test_clarifying_question_mentions_dimensions(self):
        """Generated clarifying question references affected dimensions."""
        from services.intelligence.schemas import DimensionDelta

        v = self._make_validator()
        scores = self._make_scores(
            wealth=DimensionDelta(dimension="wealth", delta=-8.0),
            health=DimensionDelta(dimension="health", delta=+8.0),
            has_tradeoff=True,
        )
        intent = self._make_intent(confidence=0.5)
        result = v.validate(scores, intent, self._make_context())
        assert "health" in result.clarifying_question.lower() or "financial" in result.clarifying_question.lower()


# ============================================================================
# Golden Scoring Cases
# ============================================================================

class TestGoldenScoringCases:
    """Test scoring policies against golden test fixtures (regression suite)."""

    def _make_engine(self):
        from services.intelligence.score_engine import ScoreEvaluationEngine
        return ScoreEvaluationEngine()

    def _make_intent(self, case):
        from services.intelligence.schemas import IntentResult
        return IntentResult(
            intent=case["intent"],
            confidence=0.95,
            original_text="golden test",
            entities=case.get("entities", {}),
        )

    def _make_context(self, case):
        from services.intelligence.schemas import (
            ContextFrame, FinancialSnapshot, HealthBaseline,
            TimeBaseline, HelmScores,
        )
        overrides = case.get("context_overrides", {})
        kwargs = {"user_id": "golden-test"}

        if "financial" in overrides:
            kwargs["financial"] = FinancialSnapshot(**{
                "total_balance": 10000, "monthly_income": 5000,
                "monthly_expenses": 3000, **overrides["financial"]
            })
        if "health" in overrides:
            kwargs["health"] = HealthBaseline(**{
                "sleep_hours_avg": 7, "sleep_quality": 60,
                "activity_level": 50, **overrides["health"]
            })
        if "time" in overrides:
            kwargs["time"] = TimeBaseline(**{
                "commute_minutes": 30, "productivity_score": 50,
                **overrides["time"]
            })

        return ContextFrame(**kwargs)

    def _load_cases(self):
        # Import directly from fixtures
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from fixtures.golden_scoring_cases import GOLDEN_CASES
        return GOLDEN_CASES

    def test_all_golden_cases(self):
        """Every golden case must produce the expected deltas and net impact."""
        engine = self._make_engine()
        cases = self._load_cases()

        failures = []
        for case in cases:
            intent = self._make_intent(case)
            context = self._make_context(case)
            scores = engine.evaluate(intent, context)

            errors = []
            if scores.wealth.delta != case["expected_wealth_delta"]:
                errors.append(f"wealth: got {scores.wealth.delta}, expected {case['expected_wealth_delta']}")
            if scores.health.delta != case["expected_health_delta"]:
                errors.append(f"health: got {scores.health.delta}, expected {case['expected_health_delta']}")
            if scores.time.delta != case["expected_time_delta"]:
                errors.append(f"time: got {scores.time.delta}, expected {case['expected_time_delta']}")
            if scores.net_impact != case["expected_net_impact"]:
                errors.append(f"net: got {scores.net_impact}, expected {case['expected_net_impact']}")
            if scores.has_tradeoff != case["expected_tradeoff"]:
                errors.append(f"tradeoff: got {scores.has_tradeoff}, expected {case['expected_tradeoff']}")

            if errors:
                failures.append(f"  {case['id']} ({case['intent']}): {'; '.join(errors)}")

        if failures:
            pytest.fail(
                f"Golden case failures ({len(failures)}/{len(cases)}):\n"
                + "\n".join(failures)
            )

    def test_golden_case_count(self):
        """Ensure we have minimum golden case coverage."""
        cases = self._load_cases()
        assert len(cases) >= 15, f"Expected >= 15 golden cases, got {len(cases)}"


# ============================================================================
# New Scoring Policy Tests (Phase 2)
# ============================================================================

class TestNewScoringPolicies:
    """Tests for the 10 new scoring policies added in Phase 2."""

    def _make_engine(self):
        from services.intelligence.score_engine import ScoreEvaluationEngine
        return ScoreEvaluationEngine()

    def _make_intent(self, name, **entities):
        from services.intelligence.schemas import IntentResult
        return IntentResult(intent=name, confidence=0.95, original_text="test", entities=entities)

    def _make_context(self, **overrides):
        from services.intelligence.schemas import ContextFrame, FinancialSnapshot, HealthBaseline, TimeBaseline
        defaults = {"user_id": "test"}
        if "financial" in overrides:
            defaults["financial"] = FinancialSnapshot(**overrides.pop("financial"))
        if "health" in overrides:
            defaults["health"] = HealthBaseline(**overrides.pop("health"))
        if "time" in overrides:
            defaults["time"] = TimeBaseline(**overrides.pop("time"))
        defaults.update(overrides)
        return ContextFrame(**defaults)

    def test_subscription_review_high_expense(self):
        engine = self._make_engine()
        intent = self._make_intent("subscription_review")
        ctx = self._make_context(financial={"monthly_expenses": 4000, "monthly_income": 5000})
        scores = engine.evaluate(intent, ctx)
        assert scores.wealth.delta == 4.0

    def test_subscription_review_low_expense(self):
        engine = self._make_engine()
        intent = self._make_intent("subscription_review")
        ctx = self._make_context(financial={"monthly_expenses": 2000, "monthly_income": 5000})
        scores = engine.evaluate(intent, ctx)
        assert scores.wealth.delta == 2.0

    def test_budget_alert_near_limit(self):
        engine = self._make_engine()
        intent = self._make_intent("budget_alert")
        ctx = self._make_context(financial={"monthly_expenses": 4500, "monthly_income": 5000})
        scores = engine.evaluate(intent, ctx)
        assert scores.wealth.delta == 5.0  # > 80% ratio

    def test_salary_analysis(self):
        engine = self._make_engine()
        intent = self._make_intent("salary_analysis")
        ctx = self._make_context(financial={"monthly_income": 8000})
        scores = engine.evaluate(intent, ctx)
        assert scores.wealth.delta == 2.0

    def test_net_worth_high_debt(self):
        engine = self._make_engine()
        intent = self._make_intent("net_worth_check")
        ctx = self._make_context(financial={"total_balance": 10000, "total_debt": 8000})
        scores = engine.evaluate(intent, ctx)
        assert scores.wealth.delta == 4.0  # High debt ratio

    def test_expense_categorize(self):
        engine = self._make_engine()
        intent = self._make_intent("expense_categorize")
        ctx = self._make_context(financial={"monthly_expenses": 4000, "monthly_income": 5000})
        scores = engine.evaluate(intent, ctx)
        assert scores.wealth.delta == 3.0  # > 70% ratio

    def test_hydration_active_user(self):
        engine = self._make_engine()
        intent = self._make_intent("hydration_reminder")
        ctx = self._make_context(health={"activity_level": 75})
        scores = engine.evaluate(intent, ctx)
        assert scores.health.delta == 3.0

    def test_deadline_low_productivity(self):
        engine = self._make_engine()
        intent = self._make_intent("deadline_reminder")
        ctx = self._make_context(time={"productivity_score": 30})
        scores = engine.evaluate(intent, ctx)
        assert scores.time.delta == 5.0

    def test_productivity_report(self):
        engine = self._make_engine()
        intent = self._make_intent("productivity_report")
        ctx = self._make_context(time={"productivity_score": 40})
        scores = engine.evaluate(intent, ctx)
        assert scores.time.delta == 3.0  # < 50 threshold

    def test_health_report(self):
        engine = self._make_engine()
        intent = self._make_intent("health_report")
        ctx = self._make_context()
        scores = engine.evaluate(intent, ctx)
        assert scores.health.delta == 2.0


# ============================================================================
# Policy Versioning Tests
# ============================================================================

class TestPolicyVersioning:
    """Tests for policy set versioning."""

    def test_policy_set_version_exists(self):
        from services.intelligence.score_engine import POLICY_SET_VERSION
        assert POLICY_SET_VERSION
        parts = POLICY_SET_VERSION.split(".")
        assert len(parts) == 3  # major.minor.patch

    def test_policy_set_version_2(self):
        from services.intelligence.score_engine import POLICY_SET_VERSION
        assert POLICY_SET_VERSION.startswith("2.")

    def test_all_policies_have_version(self):
        from services.intelligence.score_engine import SCORING_POLICIES
        for name, policy in SCORING_POLICIES.items():
            assert policy.version, f"Policy '{name}' missing version"

    def test_policy_count_at_least_35(self):
        from services.intelligence.score_engine import SCORING_POLICIES
        assert len(SCORING_POLICIES) >= 35, f"Only {len(SCORING_POLICIES)} policies"


# ============================================================================
# Schema Phase 2 Tests
# ============================================================================

class TestPhase2Schemas:
    """Tests for Phase 2 schema additions."""

    def test_cost_summary_schema(self):
        from services.intelligence.schemas import CostSummary
        cs = CostSummary(tier=1, total_tokens=500, estimated_cost_usd=0.005)
        assert cs.total_tokens == 500

    def test_stage_timings_has_tradeoff(self):
        from services.intelligence.schemas import StageTimings
        t = StageTimings()
        assert hasattr(t, "tradeoff_validation_ms")

    def test_pipeline_trace_has_cost_and_tradeoff(self):
        from services.intelligence.schemas import PipelineTrace
        t = PipelineTrace(user_id="u1")
        assert hasattr(t, "cost_summary")
        assert hasattr(t, "tradeoff_resolution")

    def test_pipeline_result_has_tradeoff(self):
        from services.intelligence.schemas import PipelineResult, ResponseEnvelope, PipelineTrace
        r = PipelineResult(
            response=ResponseEnvelope(text="hi"),
            trace=PipelineTrace(user_id="u1"),
            tradeoff_resolution="proceed",
        )
        assert r.tradeoff_resolution == "proceed"
