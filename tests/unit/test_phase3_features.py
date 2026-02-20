"""
Phase 3 Unit Tests — Hardening + New Modules.

Tests: Cache event-driven invalidation, CLARIFY/ESCALATE boundary,
       SafeMinimalContract, Execution Policy Engine, Budget Envelopes,
       Metrics Engine, Policy Governance.
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))


# ============================================================================
# Cache Event-Driven Invalidation Tests
# ============================================================================

class TestCacheInvalidation:
    """Tests for event-driven cache invalidation and versioned keys."""

    def _make_cache(self):
        from services.intelligence.cache import PipelineCache
        return PipelineCache(redis_url=None)

    def _make_model(self, name="Test"):
        from services.intelligence.schemas import ContextFrame
        return ContextFrame(user_id="test-user", user_name=name)

    def test_versioned_key_format(self):
        cache = self._make_cache()
        key = cache._build_key("ctx", "user1")
        assert key.startswith("helm:ctx:user1:v")

    def test_version_bumps_on_invalidation(self):
        cache = self._make_cache()
        v0 = cache.get_user_version("user1")
        cache._bump_version("user1")
        v1 = cache.get_user_version("user1")
        assert v1 == v0 + 1

    def test_invalidation_busts_cache(self):
        """After bumping version, old cached data is inaccessible."""
        from services.intelligence.schemas import ContextFrame
        cache = self._make_cache()
        model = self._make_model()
        cache.set("ctx", "user1", model)

        # Data accessible at current version
        result = cache.get("ctx", "user1", ContextFrame)
        assert result is not None

        # Bump version → old data is at v0, new lookups use v1
        cache._bump_version("user1")
        result = cache.get("ctx", "user1", ContextFrame)
        assert result is None  # Stale — version mismatch

    def test_invalidate_on_transaction(self):
        from services.intelligence.cache import InvalidationEvent
        from services.intelligence.schemas import ContextFrame
        cache = self._make_cache()
        model = self._make_model()
        cache.set("ctx", "user1", model)

        cache.invalidate_on_event("user1", InvalidationEvent.TRANSACTION_LOGGED)
        result = cache.get("ctx", "user1", ContextFrame)
        assert result is None

    def test_invalidate_on_crisis_toggle(self):
        from services.intelligence.cache import InvalidationEvent
        from services.intelligence.schemas import ContextFrame
        cache = self._make_cache()
        cache.set("ctx", "user1", self._make_model())

        cache.invalidate_on_event("user1", InvalidationEvent.CRISIS_MODE_TOGGLED)
        assert cache.get("ctx", "user1", ContextFrame) is None

    def test_invalidate_on_preference_change(self):
        from services.intelligence.cache import InvalidationEvent
        from services.intelligence.schemas import ContextFrame
        cache = self._make_cache()
        cache.set("ctx", "user1", self._make_model())

        cache.invalidate_on_event("user1", InvalidationEvent.PREFERENCE_CHANGED)
        assert cache.get("ctx", "user1", ContextFrame) is None

    def test_invalidation_event_enum_count(self):
        from services.intelligence.cache import InvalidationEvent
        assert len(InvalidationEvent) >= 7

    def test_all_events_have_mapping(self):
        from services.intelligence.cache import InvalidationEvent, _EVENT_INVALIDATION_MAP
        for event in InvalidationEvent:
            assert event in _EVENT_INVALIDATION_MAP

    def test_stats_includes_versions(self):
        cache = self._make_cache()
        cache._bump_version("user1")
        stats = cache.stats()
        assert "versions" in stats
        assert stats["versions"] >= 1

    def test_non_ctx_namespace_not_versioned(self):
        cache = self._make_cache()
        key = cache._build_key("intent", "some_hash")
        assert key == "helm:intent:some_hash"  # No version suffix


# ============================================================================
# CLARIFY vs ESCALATE Boundary Tests
# ============================================================================

class TestClarifyEscalateBoundary:
    """Tests for scalar-resolvable vs multi-variable intent classification."""

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

    def _make_intent(self, name, confidence=0.5):
        from services.intelligence.schemas import IntentResult
        return IntentResult(intent=name, confidence=confidence, original_text="test")

    def _make_context(self):
        from services.intelligence.schemas import ContextFrame
        return ContextFrame(user_id="test")

    def test_multi_variable_always_escalates(self):
        """Multi-variable intents always escalate regardless of confidence."""
        from services.intelligence.tradeoff_validator import TradeoffResolution
        v = self._make_validator()
        for intent_name in ["career_change", "relocation_analysis", "tradeoff_analysis"]:
            result = v.validate(
                self._make_scores(), self._make_intent(intent_name, confidence=0.95),
                self._make_context()
            )
            assert result.resolution == TradeoffResolution.ESCALATE, f"{intent_name} didn't escalate"

    def test_scalar_resolvable_clarifies_on_low_confidence(self):
        """Scalar-resolvable intents clarify when confidence is low."""
        from services.intelligence.tradeoff_validator import TradeoffResolution
        v = self._make_validator()
        for intent_name in ["mobility_booking", "schedule_event", "bill_payment"]:
            result = v.validate(
                self._make_scores(), self._make_intent(intent_name, confidence=0.6),
                self._make_context()
            )
            assert result.resolution == TradeoffResolution.CLARIFY, f"{intent_name} didn't clarify"

    def test_scalar_resolvable_proceeds_on_high_confidence(self):
        """Scalar-resolvable intents proceed when confidence is high."""
        from services.intelligence.tradeoff_validator import TradeoffResolution
        v = self._make_validator()
        result = v.validate(
            self._make_scores(), self._make_intent("mobility_booking", confidence=0.95),
            self._make_context()
        )
        assert result.resolution == TradeoffResolution.PROCEED

    def test_scalar_clarify_has_targeted_question(self):
        """Scalar clarify produces intent-specific question."""
        from services.intelligence.tradeoff_validator import _SCALAR_QUESTIONS
        v = self._make_validator()
        result = v.validate(
            self._make_scores(), self._make_intent("mobility_booking", confidence=0.6),
            self._make_context()
        )
        assert result.clarifying_question == _SCALAR_QUESTIONS["mobility_booking"]

    def test_scalar_and_multi_sets_populated(self):
        from services.intelligence.tradeoff_validator import SCALAR_RESOLVABLE_INTENTS, MULTI_VARIABLE_INTENTS
        assert len(SCALAR_RESOLVABLE_INTENTS) >= 10
        assert len(MULTI_VARIABLE_INTENTS) >= 5
        # No overlap
        assert SCALAR_RESOLVABLE_INTENTS.isdisjoint(MULTI_VARIABLE_INTENTS)


# ============================================================================
# SAFE_MINIMAL Contract Tests
# ============================================================================

class TestSafeMinimalContract:
    """Tests for SafeMinimalContract invariants."""

    def _make_validator(self):
        from services.intelligence.tradeoff_validator import TradeoffValidator
        return TradeoffValidator()

    def _make_context(self, **overrides):
        from services.intelligence.schemas import ContextFrame, HelmScores
        return ContextFrame(user_id="test", **overrides)

    def test_crisis_produces_contract(self):
        """Crisis-mode SAFE_MINIMAL always produces a valid contract."""
        from services.intelligence.schemas import DimensionDelta, HelmScores
        v = self._make_validator()
        from services.intelligence.schemas import ScoreDeltas
        scores = ScoreDeltas(
            wealth=DimensionDelta(dimension="wealth", delta=-10.0),
            health=DimensionDelta(dimension="health"),
            time=DimensionDelta(dimension="time"),
        )
        context = self._make_context(
            crisis_mode=True,
            crisis_dimensions=["wealth"],
            helm_scores=HelmScores(wealth=25),
        )
        from services.intelligence.schemas import IntentResult
        intent = IntentResult(intent="test", confidence=0.9, original_text="test")
        result = v.validate(scores, intent, context)

        assert result.safe_minimal_contract is not None
        assert result.safe_minimal_contract.validate() is True

    def test_contract_invariants(self):
        """All contract invariants hold."""
        from services.intelligence.tradeoff_validator import SafeMinimalContract
        contract = SafeMinimalContract(
            offer_one_next_action="Do this",
            offer_one_question="Want help?",
        )
        assert contract.no_spending_commitments is True
        assert contract.no_irreversible_actions is True
        assert contract.only_reversible_suggestions is True
        assert contract.validate() is True

    def test_contract_fails_without_next_action(self):
        from services.intelligence.tradeoff_validator import SafeMinimalContract
        contract = SafeMinimalContract(offer_one_question="Want help?")
        assert contract.validate() is False

    def test_contract_has_stabilization_steps(self):
        """Contract includes dimension-specific stabilization steps."""
        from services.intelligence.schemas import DimensionDelta, HelmScores, ScoreDeltas, IntentResult
        v = self._make_validator()
        scores = ScoreDeltas(
            wealth=DimensionDelta(dimension="wealth", delta=-10.0),
            health=DimensionDelta(dimension="health"),
            time=DimensionDelta(dimension="time"),
        )
        context = self._make_context(
            crisis_mode=True,
            crisis_dimensions=["wealth"],
            helm_scores=HelmScores(wealth=25),
        )
        intent = IntentResult(intent="test", confidence=0.9, original_text="test")
        result = v.validate(scores, intent, context)

        assert len(result.safe_minimal_contract.stabilization_steps) > 0


# ============================================================================
# Execution Policy Engine Tests
# ============================================================================

class TestExecutionPolicy:
    """Tests for the Execution Policy Engine."""

    def _make_engine(self):
        from services.intelligence.execution_policy import ExecutionPolicyEngine
        return ExecutionPolicyEngine()

    def test_read_only_intent_always_allows(self):
        from services.intelligence.execution_policy import ActionGate
        engine = self._make_engine()
        result = engine.evaluate(
            intent_type="balance_check", tier=0, execution_id="exec-001"
        )
        assert result.gate == ActionGate.ALLOW

    def test_medium_risk_requires_confirm(self):
        from services.intelligence.execution_policy import ActionGate
        engine = self._make_engine()
        result = engine.evaluate(
            intent_type="bill_payment", tier=1, execution_id="exec-002"
        )
        assert result.gate == ActionGate.CONFIRM
        assert result.requires_confirmation is True

    def test_high_risk_requires_confirm(self):
        from services.intelligence.execution_policy import ActionGate
        engine = self._make_engine()
        result = engine.evaluate(
            intent_type="car_purchase", tier=2, execution_id="exec-003"
        )
        assert result.gate == ActionGate.CONFIRM

    def test_critical_risk_requires_2fa(self):
        from services.intelligence.execution_policy import ActionGate
        engine = self._make_engine()
        result = engine.evaluate(
            intent_type="career_change", tier=3, execution_id="exec-004"
        )
        assert result.gate == ActionGate.CONFIRM_2FA

    def test_safe_minimal_denies_all(self):
        from services.intelligence.execution_policy import ActionGate
        engine = self._make_engine()
        result = engine.evaluate(
            intent_type="bill_payment", tier=1, execution_id="exec-005",
            tradeoff_resolution="safe_minimal"
        )
        assert result.gate == ActionGate.DENY

    def test_crisis_mode_denies_high_risk(self):
        from services.intelligence.execution_policy import ActionGate
        engine = self._make_engine()
        result = engine.evaluate(
            intent_type="car_purchase", tier=2, execution_id="exec-006",
            crisis_mode=True
        )
        assert result.gate == ActionGate.DENY

    def test_idempotency_blocks_duplicate(self):
        from services.intelligence.execution_policy import ActionGate
        engine = self._make_engine()
        engine.evaluate(intent_type="balance_check", tier=0, execution_id="exec-007")
        # Second call with same execution_id
        result = engine.evaluate(intent_type="balance_check", tier=0, execution_id="exec-007")
        assert result.gate == ActionGate.DENY
        assert "Duplicate" in result.reason

    def test_no_consent_denies_non_readonly(self):
        from services.intelligence.execution_policy import ActionGate
        engine = self._make_engine()
        result = engine.evaluate(
            intent_type="bill_payment", tier=1, execution_id="exec-008",
            user_consent=False,
        )
        assert result.gate == ActionGate.DENY

    def test_partner_unavailable_denies(self):
        from services.intelligence.execution_policy import ActionGate
        engine = self._make_engine()
        result = engine.evaluate(
            intent_type="mobility_booking", tier=1, execution_id="exec-009",
            partner_available=False,
            action_types=["execute_mobility"],
        )
        assert result.gate == ActionGate.DENY

    def test_rollback_allows_reuse(self):
        from services.intelligence.execution_policy import ActionGate
        engine = self._make_engine()
        engine.evaluate(intent_type="balance_check", tier=0, execution_id="exec-010")
        engine.rollback("exec-010")
        result = engine.evaluate(intent_type="balance_check", tier=0, execution_id="exec-010")
        assert result.gate == ActionGate.ALLOW

    def test_risk_class_lookup(self):
        from services.intelligence.execution_policy import ExecutionPolicyEngine, RiskClass
        assert ExecutionPolicyEngine.get_risk_class("balance_check") == RiskClass.NONE
        assert ExecutionPolicyEngine.get_risk_class("car_purchase") == RiskClass.HIGH
        assert ExecutionPolicyEngine.get_risk_class("career_change") == RiskClass.CRITICAL


# ============================================================================
# Budget Envelope Tests
# ============================================================================

class TestBudgetEnvelope:
    """Tests for per-user budget envelopes."""

    def _make_engine(self):
        from services.intelligence.budget_envelope import BudgetEnvelopeEngine
        return BudgetEnvelopeEngine()

    def test_free_plan_defaults(self):
        from services.intelligence.budget_envelope import UserPlan
        engine = self._make_engine()
        env = engine.compute(user_plan=UserPlan.FREE)
        assert env.max_tier == 2
        assert env.max_input_tokens == 800

    def test_premium_plan_defaults(self):
        from services.intelligence.budget_envelope import UserPlan
        engine = self._make_engine()
        env = engine.compute(user_plan=UserPlan.PREMIUM)
        assert env.max_tier == 3
        assert env.max_input_tokens == 4000

    def test_crisis_mode_caps_tier(self):
        from services.intelligence.budget_envelope import UserPlan
        engine = self._make_engine()
        env = engine.compute(user_plan=UserPlan.PREMIUM, crisis_mode=True)
        assert env.max_tier <= 2

    def test_crisis_multi_dimension_boosts_clarify(self):
        from services.intelligence.budget_envelope import UserPlan
        engine = self._make_engine()
        env = engine.compute(
            user_plan=UserPlan.STANDARD,
            crisis_mode=True,
            crisis_dimensions=["wealth", "health"],
        )
        assert env.clarify_confidence_boost >= 0.10

    def test_volatility_boosts_clarify(self):
        engine = self._make_engine()
        env = engine.compute(high_volatility=True)
        assert env.clarify_confidence_boost >= 0.15

    def test_explicit_max_tier_override(self):
        engine = self._make_engine()
        env = engine.compute(explicit_max_tier=1)
        assert env.max_tier == 1

    def test_force_deterministic(self):
        engine = self._make_engine()
        env = engine.compute(explicit_force_deterministic=True)
        assert env.force_deterministic is True
        assert env.max_tier == 0

    def test_reason_tracking(self):
        engine = self._make_engine()
        env = engine.compute(crisis_mode=True, high_volatility=True)
        assert "crisis_mode" in env.reason
        assert "high_volatility" in env.reason


# ============================================================================
# Metrics Engine Tests
# ============================================================================

class TestMetricsEngine:
    """Tests for the 5 health metrics."""

    def _make_engine(self):
        from services.intelligence.metrics import MetricsEngine
        return MetricsEngine()

    def test_empty_data(self):
        engine = self._make_engine()
        report = engine.compute([], [])
        assert report.escalation.total_requests == 0
        assert report.cost.total_cost_usd == 0

    def test_escalation_rate(self):
        engine = self._make_engine()
        decisions = [
            {"tier": 0, "intent_type": "greeting"},
            {"tier": 1, "intent_type": "balance_check"},
            {"tier": 3, "intent_type": "career_change"},
            {"tier": 3, "intent_type": "relocation_analysis"},
        ]
        report = engine.compute(decisions, [])
        assert report.escalation.total_requests == 4
        assert report.escalation.escalated_requests == 2
        assert report.escalation.escalation_rate == 50.0

    def test_safe_minimal_frequency(self):
        engine = self._make_engine()
        decisions = [
            {"tradeoff_resolution": "proceed", "user_id": "u1"},
            {"tradeoff_resolution": "safe_minimal", "user_id": "u1"},
            {"tradeoff_resolution": "safe_minimal", "user_id": "u1"},
            {"tradeoff_resolution": "proceed", "user_id": "u2"},
        ]
        report = engine.compute(decisions, [])
        assert report.safe_minimal.safe_minimal_count == 2
        assert report.safe_minimal.frequency == 50.0
        assert report.safe_minimal.repeat_rate == 100.0  # u1 hit it twice

    def test_cost_per_resolved(self):
        engine = self._make_engine()
        decisions = [
            {"estimated_cost_usd": 0.01, "tier": 1},
            {"estimated_cost_usd": 0.05, "tier": 3},
        ]
        outcomes = [
            {"completed": True},
            {"completed": False},
        ]
        report = engine.compute(decisions, outcomes)
        assert report.cost.total_cost_usd == pytest.approx(0.06)
        assert report.cost.total_resolved == 1
        assert report.cost.cost_per_resolved_usd == pytest.approx(0.06)

    def test_completion_rate(self):
        engine = self._make_engine()
        outcomes = [
            {"completed": True, "time_to_complete_ms": 100, "user_satisfaction": 1},
            {"completed": True, "time_to_complete_ms": 200, "user_satisfaction": -1},
            {"completed": False, "time_to_complete_ms": 0, "user_satisfaction": 0},
        ]
        report = engine.compute([], outcomes)
        assert report.completion.total_actions == 3
        assert report.completion.completed_actions == 2
        assert report.completion.completion_rate == pytest.approx(66.67, abs=0.1)
        assert report.completion.avg_time_to_complete_ms == 150.0

    def test_report_to_dict(self):
        engine = self._make_engine()
        report = engine.compute([], [])
        d = report.to_dict()
        assert "escalation" in d
        assert "clarify" in d
        assert "cost" in d
        assert "completion" in d


# ============================================================================
# Policy Governance Tests
# ============================================================================

class TestPolicyGovernance:
    """Tests for policy governance fields and validate_policy_registry."""

    def test_scoring_policy_has_governance_fields(self):
        from services.intelligence.score_engine import ScoringPolicy
        p = ScoringPolicy(name="test", owner="wealth-team")
        assert p.owner == "wealth-team"
        assert p.deprecated is False
        assert p.superseded_by is None

    def test_validate_registry_runs(self):
        from services.intelligence.score_engine import validate_policy_registry
        issues = validate_policy_registry()
        assert isinstance(issues, dict)
        assert "missing" in issues
        assert "orphaned" in issues
        assert "deprecated" in issues
        assert "superseded" in issues

    def test_no_deprecated_policies_in_active_use(self):
        from services.intelligence.score_engine import validate_policy_registry
        issues = validate_policy_registry()
        assert len(issues["deprecated"]) == 0, f"Deprecated policies in use: {issues['deprecated']}"

    def test_validate_registry_no_missing(self):
        """All intent→policy references are resolvable."""
        from services.intelligence.score_engine import validate_policy_registry
        issues = validate_policy_registry()
        assert len(issues["missing"]) == 0, f"Missing policies: {issues['missing']}"
