"""
Unit Tests for the HELM Intelligence Pipeline.

Tests all deterministic stages without any LLM or database dependency.
Every test is fast (< 10ms), isolated, and reproducible.
"""

import sys
import os
import json
import pytest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))


# ============================================================================
# Stage 1: Input Processing Tests
# ============================================================================


class TestInputProcessor:
    """Tests for Stage 1: Input Processing (fully deterministic)."""

    def _make_processor(self):
        from services.intelligence.input_processor import InputProcessor

        return InputProcessor()

    def test_basic_normalization(self):
        """Text is stripped and whitespace collapsed."""
        proc = self._make_processor()
        envelope = proc.process("  Hello   world  ", user_id="u1")
        assert envelope.normalized_text == "Hello world"
        assert envelope.raw_text == "Hello   world"  # raw preserves internal whitespace
        assert envelope.user_id == "u1"

    def test_empty_input(self):
        """Empty string normalizes to empty."""
        proc = self._make_processor()
        envelope = proc.process("", user_id="u1")
        assert envelope.normalized_text == ""

    def test_long_input_truncation(self):
        """Input longer than MAX_INPUT_LENGTH is truncated."""
        proc = self._make_processor()
        long_text = "x" * 5000
        envelope = proc.process(long_text, user_id="u1")
        assert len(envelope.normalized_text) <= 4000

    def test_control_characters_removed(self):
        """Control characters are stripped."""
        proc = self._make_processor()
        envelope = proc.process("Hello\x00World\x01", user_id="u1")
        assert "\x00" not in envelope.normalized_text
        assert "\x01" not in envelope.normalized_text

    def test_session_metadata_enrichment(self):
        """Session metadata is captured in the envelope."""
        proc = self._make_processor()
        envelope = proc.process(
            "hi",
            user_id="u1",
            session_metadata={
                "session_id": "s123",
                "device_type": "mobile",
                "locale": "ar",
                "conversation_history": [{"role": "user", "content": "old message"}],
            },
        )
        assert envelope.session_id == "s123"
        assert envelope.device_type == "mobile"
        assert envelope.locale == "ar"
        assert len(envelope.conversation_history) == 1

    def test_request_id_generated(self):
        """Each envelope gets a unique request_id."""
        proc = self._make_processor()
        e1 = proc.process("a", user_id="u1")
        e2 = proc.process("b", user_id="u1")
        assert e1.request_id != e2.request_id

    def test_attachment_parsing(self):
        """Valid attachments are parsed, unknown types are ignored."""
        proc = self._make_processor()
        envelope = proc.process(
            "hi",
            user_id="u1",
            session_metadata={
                "attachments": [
                    {"type": "transaction_receipt", "amount": 100},
                    {"type": "unknown_type", "data": "bad"},
                ],
            },
        )
        assert len(envelope.attachments) == 1
        assert envelope.attachments[0]["type"] == "transaction_receipt"

    def test_location_valid_is_captured(self):
        """Valid browser coordinates flow onto the envelope."""
        proc = self._make_processor()
        envelope = proc.process(
            "find a gym near me",
            user_id="u1",
            session_metadata={"location": {"lat": 25.2, "lng": 55.27}},
        )
        assert envelope.location == {"lat": 25.2, "lng": 55.27}

    def test_location_null_island_and_garbage_rejected(self):
        """(0,0) placeholder and malformed coords are dropped, not passed on."""
        proc = self._make_processor()
        assert (
            proc.process(
                "hi", user_id="u1", session_metadata={"location": {"lat": 0, "lng": 0}}
            ).location
            is None
        )
        assert (
            proc.process(
                "hi", user_id="u1", session_metadata={"location": {"lat": "x"}}
            ).location
            is None
        )
        assert proc.process("hi", user_id="u1").location is None


# ============================================================================
# Stage 3: Intent Classification Tests (Deterministic Pass Only)
# ============================================================================


class TestIntentTaxonomy:
    """Tests for deterministic intent matching in the taxonomy."""

    def _match(self, text):
        from services.intelligence.intent_taxonomy import match_deterministic

        return match_deterministic(text)

    # --- Wealth Intents ---
    def test_balance_check(self):
        result = self._match("What is my balance?")
        assert result is not None
        assert result[0] == "balance_check"

    def test_spending_report(self):
        result = self._match("How much did I spend last month?")
        assert result is not None
        assert result[0] == "spending_report"

    def test_financial_advisory_keyword(self):
        result = self._match("Can I afford a new laptop?")
        assert result is not None
        assert result[0] == "financial_advisory"

    def test_financial_advisory_regex(self):
        result = self._match("Should I buy that phone?")
        assert result is not None
        assert result[0] == "financial_advisory"

    def test_set_savings_goal(self):
        result = self._match("I want to save for a vacation")
        assert result is not None
        assert result[0] == "set_savings_goal"

    def test_bill_payment(self):
        result = self._match("Pay my credit card bill")
        assert result is not None
        assert result[0] == "bill_payment"

    # --- Health Intents ---
    def test_sleep_analysis(self):
        result = self._match("How did I sleep last night?")
        assert result is not None
        assert result[0] == "sleep_analysis"

    def test_stress_check(self):
        result = self._match("I'm feeling really stressed today")
        assert result is not None
        assert result[0] == "stress_check"

    def test_activity_summary(self):
        result = self._match("How many steps did I take?")
        assert result is not None
        assert result[0] == "activity_summary"

    # --- Time Intents ---
    def test_schedule_event(self):
        result = self._match("Schedule a meeting tomorrow at 3pm")
        assert result is not None
        assert result[0] == "schedule_event"

    def test_calendar_view(self):
        result = self._match("What's on my calendar today?")
        assert result is not None
        assert result[0] == "calendar_view"

    def test_focus_time(self):
        result = self._match("I need some focus time")
        assert result is not None
        assert result[0] == "focus_time_block"

    # --- Mobility Intents ---
    def test_mobility_booking(self):
        result = self._match("Book me an uber to the airport")
        assert result is not None
        assert result[0] == "mobility_booking"

    def test_mobility_price_check(self):
        result = self._match("How much is a ride to Dubai Mall?")
        assert result is not None
        assert result[0] == "mobility_price_check"

    def test_car_purchase(self):
        result = self._match("I want to buy a new car")
        assert result is not None
        assert result[0] == "car_purchase"

    # --- Lifestyle / Local Search ---
    def test_local_search_find_near_me(self):
        """A bare place-search reads as local_search, not a ride."""
        result = self._match(
            "Find some near me, tell me how far and how much they cost?"
        )
        assert result is not None
        assert result[0] == "local_search"

    def test_local_search_keyword(self):
        result = self._match("gyms nearby")
        assert result is not None
        assert result[0] == "local_search"

    def test_ride_still_wins_over_local_search(self):
        """An explicit ride request is still mobility, not local_search."""
        result = self._match("How much is an Uber to Dubai Marina?")
        assert result is not None
        assert result[0] == "mobility_price_check"

    # --- Cross-Domain ---
    def test_greeting(self):
        result = self._match("Hello!")
        assert result is not None
        assert result[0] == "greeting"

    def test_tradeoff_regex(self):
        result = self._match("Should I take the new job or stay?")
        assert result is not None
        assert result[0] == "tradeoff_analysis"

    def test_no_match_returns_none(self):
        """Completely novel input returns None (requires LLM)."""
        result = self._match("quantum entanglement theory discussion")
        assert result is None

    # --- Confidence Levels ---
    def test_keyword_match_confidence(self):
        """Keyword matches yield 0.95 confidence."""
        result = self._match("check balance")
        assert result is not None
        assert result[1] == 0.95
        assert result[2] == "keyword"

    def test_regex_match_confidence(self):
        """Regex matches yield 0.85 confidence."""
        result = self._match("can i spend 500 on shoes")
        assert result is not None
        assert result[1] == 0.85
        assert result[2] == "regex"


class TestIntentClassifier:
    """Tests for the IntentClassifier (deterministic-only mode)."""

    def _make_classifier(self):
        from services.intelligence.intent_classifier import IntentClassifier

        return IntentClassifier(llm_model=None, llm_api_key=None)

    def _make_envelope(self, text):
        from services.intelligence.schemas import InputEnvelope

        return InputEnvelope(
            user_id="test-user",
            raw_text=text,
            normalized_text=text.strip().lower(),
        )

    def _make_context(self):
        from services.intelligence.schemas import ContextFrame

        return ContextFrame(user_id="test-user")

    @pytest.mark.asyncio
    async def test_deterministic_classification(self):
        """Known intents resolve deterministically without LLM."""
        classifier = self._make_classifier()
        envelope = self._make_envelope("What is my balance?")
        context = self._make_context()
        result = await classifier.classify(envelope, context)

        assert result.intent == "balance_check"
        assert result.confidence == 0.95
        assert result.classified_by == "deterministic"
        assert result.llm_tokens_used == 0

    @pytest.mark.asyncio
    async def test_unknown_falls_to_default(self):
        """Unknown input without LLM defaults to general_conversation."""
        classifier = self._make_classifier()
        envelope = self._make_envelope("Tell me about black holes")
        context = self._make_context()
        result = await classifier.classify(envelope, context)

        assert result.intent == "general_conversation"
        assert result.classified_by == "deterministic_fallback"

    @pytest.mark.asyncio
    async def test_entity_extraction_money(self):
        """Money amounts are extracted from text."""
        classifier = self._make_classifier()
        envelope = self._make_envelope("Can I afford something for AED 5000?")
        context = self._make_context()
        result = await classifier.classify(envelope, context)

        assert result.intent == "financial_advisory"
        assert "amount" in result.entities
        assert result.entities["amount"] == 5000.0

    @pytest.mark.asyncio
    async def test_entity_extraction_location(self):
        """Locations are extracted for mobility intents."""
        classifier = self._make_classifier()
        envelope = self._make_envelope("book uber from home to dubai mall")
        context = self._make_context()
        result = await classifier.classify(envelope, context)

        assert result.intent == "mobility_booking"
        assert result.entities.get("start_location") is not None
        assert result.entities.get("destination") is not None


# ============================================================================
# Stage 4: Score Evaluation Engine Tests
# ============================================================================


class TestScoreEngine:
    """Tests for Stage 4: Score Evaluation (fully deterministic)."""

    def _make_engine(self):
        from services.intelligence.score_engine import ScoreEvaluationEngine

        return ScoreEvaluationEngine()

    def _make_intent(self, intent_name, **entities):
        from services.intelligence.schemas import IntentResult

        return IntentResult(
            intent=intent_name,
            confidence=0.95,
            original_text="test",
            entities=entities,
        )

    def _make_context(self, **overrides):
        from services.intelligence.schemas import (
            ContextFrame,
            FinancialSnapshot,
            HealthBaseline,
            HelmScores,
        )

        defaults = {
            "user_id": "test-user",
            "helm_scores": HelmScores(wealth=60, health=55, time=50),
            "financial": FinancialSnapshot(
                total_balance=10000, monthly_income=5000, monthly_expenses=3000
            ),
            "health": HealthBaseline(
                sleep_hours_avg=7, sleep_quality=60, activity_level=50
            ),
        }
        defaults.update(overrides)
        return ContextFrame(**defaults)

    def test_balance_check_neutral(self):
        """Checking balance has no scoring policy — returns neutral."""
        engine = self._make_engine()
        intent = self._make_intent("balance_check")
        context = self._make_context()
        scores = engine.evaluate(intent, context)

        # balance_check has no scoring_policy in taxonomy
        assert scores.wealth.delta == 0
        assert scores.health.delta == 0
        assert scores.time.delta == 0
        assert scores.net_impact == "neutral"

    def test_spending_report_positive(self):
        """Viewing spending report is slightly positive for wealth awareness."""
        engine = self._make_engine()
        intent = self._make_intent("spending_report")
        context = self._make_context()
        scores = engine.evaluate(intent, context)

        assert scores.wealth.delta == 1.0
        assert scores.wealth.direction == "up"
        assert scores.net_impact == "positive"

    def test_mobility_booking_tradeoff(self):
        """Booking a ride has tradeoff: -wealth, +time."""
        engine = self._make_engine()
        intent = self._make_intent("mobility_booking")
        context = self._make_context()
        scores = engine.evaluate(intent, context)

        assert scores.wealth.delta < 0  # Costs money
        assert scores.time.delta > 0  # Saves time
        assert scores.has_tradeoff is True
        assert scores.net_impact == "mixed"

    def test_car_purchase_large_wealth_impact(self):
        """Car purchase has significant negative wealth impact."""
        engine = self._make_engine()
        intent = self._make_intent("car_purchase")
        context = self._make_context()
        scores = engine.evaluate(intent, context)

        assert scores.wealth.delta < -5  # Significant negative
        assert scores.time.delta > 0  # Time savings from commute
        assert "car_purchase" in scores.policies_applied

    def test_financial_advisory_with_large_amount(self):
        """Large spending amount relative to income yields large negative delta."""
        engine = self._make_engine()
        intent = self._make_intent("financial_advisory", amount=3000)
        context = self._make_context()  # monthly_income=5000
        scores = engine.evaluate(intent, context)

        # 3000/5000 = 60% → > 50% threshold → -15 delta
        assert scores.wealth.delta == -15.0

    def test_financial_advisory_small_amount(self):
        """Small spending amount yields small negative delta."""
        engine = self._make_engine()
        intent = self._make_intent("financial_advisory", amount=100)
        context = self._make_context()  # monthly_income=5000
        scores = engine.evaluate(intent, context)

        # 100/5000 = 2% → < 10% threshold → -2 delta
        assert scores.wealth.delta == -2.0

    def test_goal_set_positive(self):
        """Setting a savings goal is positive for wealth."""
        engine = self._make_engine()
        intent = self._make_intent("set_savings_goal", target_amount=10000)
        context = self._make_context()
        scores = engine.evaluate(intent, context)

        assert scores.wealth.delta > 0
        assert scores.net_impact == "positive"

    def test_workout_plan_tradeoff(self):
        """Workout plan: +health, -time."""
        engine = self._make_engine()
        intent = self._make_intent("workout_plan")
        context = self._make_context()
        scores = engine.evaluate(intent, context)

        assert scores.health.delta > 0
        assert scores.time.delta < 0
        assert scores.has_tradeoff is True

    def test_focus_time_positive(self):
        """Blocking focus time is positive for both time and health."""
        engine = self._make_engine()
        intent = self._make_intent("focus_time_block")
        context = self._make_context()
        scores = engine.evaluate(intent, context)

        assert scores.time.delta > 0
        assert scores.health.delta > 0
        assert scores.net_impact == "positive"

    def test_score_clamping(self):
        """Deltas are clamped to [-100, +100]."""
        engine = self._make_engine()
        intent = self._make_intent("spending_report")
        context = self._make_context()
        scores = engine.evaluate(intent, context)

        assert -100 <= scores.wealth.delta <= 100
        assert -100 <= scores.health.delta <= 100
        assert -100 <= scores.time.delta <= 100

    def test_crisis_mode_amplification(self):
        """In crisis mode (wealth < 30), negative wealth deltas are amplified."""
        from services.intelligence.schemas import HelmScores

        engine = self._make_engine()
        intent = self._make_intent("financial_advisory", amount=2000)
        context = self._make_context(
            helm_scores=HelmScores(wealth=25, health=60, time=50),
            crisis_mode=True,
            crisis_dimensions=["wealth"],
        )
        scores = engine.evaluate(intent, context)

        # Should be amplified (x1.3) compared to normal
        assert scores.crisis_override is True
        assert scores.wealth.delta < -5  # Amplified

    def test_goal_impact_detected(self):
        """Negative wealth impact triggers goal impact warning."""
        engine = self._make_engine()
        intent = self._make_intent("financial_advisory", amount=3000)
        context = self._make_context(
            life_goals=[
                {"title": "Emergency Fund", "priority": "high", "target_amount": 5000}
            ]
        )
        scores = engine.evaluate(intent, context)

        assert len(scores.goal_impacts) > 0
        assert "Emergency Fund" in scores.goal_impacts[0]

    def test_debt_guardrail(self):
        """Spending exceeding total balance triggers CRITICAL warning."""
        from services.intelligence.schemas import FinancialSnapshot

        engine = self._make_engine()
        intent = self._make_intent("financial_advisory", amount=15000)
        context = self._make_context(
            financial=FinancialSnapshot(total_balance=10000, monthly_income=5000)
        )
        scores = engine.evaluate(intent, context)

        assert any("CRITICAL" in gi for gi in scores.goal_impacts)

    def test_no_policy_returns_neutral(self):
        """Intent with no scoring policy returns neutral deltas."""
        engine = self._make_engine()
        intent = self._make_intent("greeting")
        context = self._make_context()
        scores = engine.evaluate(intent, context)

        assert scores.wealth.delta == 0
        assert scores.health.delta == 0
        assert scores.time.delta == 0
        assert scores.net_impact == "neutral"

    def test_policies_applied_tracked(self):
        """Applied policies are listed in the trace."""
        engine = self._make_engine()
        intent = self._make_intent("mobility_booking")
        context = self._make_context()
        scores = engine.evaluate(intent, context)

        assert "mobility_booking" in scores.policies_applied


# ============================================================================
# Stage 5: Decision Synthesis Tests (Template Path Only)
# ============================================================================


class TestDecisionSynthesizer:
    """Tests for Stage 5: Decision Synthesis (template path)."""

    def _make_synthesizer(self):
        from services.intelligence.decision_synthesizer import DecisionSynthesizer

        return DecisionSynthesizer(heavy_llm_model=None, llm_api_key=None)

    def _make_intent(self, intent_name, confidence=0.95, original_text="test"):
        from services.intelligence.schemas import IntentResult

        return IntentResult(
            intent=intent_name,
            confidence=confidence,
            original_text=original_text,
        )

    def _make_scores(self):
        from services.intelligence.schemas import ScoreDeltas

        return ScoreDeltas()

    def _make_context(self):
        from services.intelligence.schemas import ContextFrame

        return ContextFrame(user_id="test-user")

    @pytest.mark.asyncio
    async def test_template_synthesis(self):
        """Known intent resolves via template without LLM."""
        synth = self._make_synthesizer()
        intent = self._make_intent("balance_check")
        scores = self._make_scores()
        context = self._make_context()
        plan = await synth.synthesize(intent, scores, context)

        assert plan.synthesized_by == "template"
        assert plan.response_template_id == "balance_report"
        assert len(plan.steps) == 1
        assert plan.steps[0].action_type.value == "respond_only"
        assert plan.llm_tokens_used == 0

    @pytest.mark.asyncio
    async def test_mobility_booking_requires_confirmation(self):
        """Mobility booking step requires confirmation."""
        synth = self._make_synthesizer()
        intent = self._make_intent("mobility_booking")
        scores = self._make_scores()
        context = self._make_context()
        plan = await synth.synthesize(intent, scores, context)

        assert any(s.requires_confirmation for s in plan.steps)
        assert plan.steps[-1].action_type.value == "execute_mobility"

    @pytest.mark.asyncio
    async def test_career_change_needs_escalation(self):
        """Career change intent always triggers escalation intent, but falls back to template without LLM."""
        synth = self._make_synthesizer()
        intent = self._make_intent("career_change")
        scores = self._make_scores()
        context = self._make_context()
        plan = await synth.synthesize(intent, scores, context)

        # No heavy LLM available → falls back to template
        assert plan.synthesized_by == "template"

    @pytest.mark.asyncio
    async def test_escalation_detection(self):
        """_should_escalate correctly identifies escalation triggers."""
        from services.intelligence.schemas import ScoreDeltas, DimensionDelta

        synth = self._make_synthesizer()

        # Always-escalate intent
        intent = self._make_intent("tradeoff_analysis")
        scores = self._make_scores()
        assert synth._should_escalate(intent, scores) is True

        # Low confidence
        intent = self._make_intent("general_conversation", confidence=0.5)
        assert synth._should_escalate(intent, scores) is True

        # High confidence, normal intent → no escalation
        intent = self._make_intent("balance_check", confidence=0.95)
        assert synth._should_escalate(intent, scores) is False


# ============================================================================
# Stage 6: Response Generation Tests (Template Path Only)
# ============================================================================


class TestResponseGenerator:
    """Tests for Stage 6: Response Generation (template path)."""

    def _make_generator(self):
        from services.intelligence.response_generator import ResponseGenerator

        return ResponseGenerator(llm_model=None, llm_api_key=None)

    def _make_intent(self, intent_name, **entities):
        from services.intelligence.schemas import IntentResult

        return IntentResult(
            intent=intent_name,
            confidence=0.95,
            original_text="test",
            entities=entities,
        )

    def _make_context(self):
        from services.intelligence.schemas import (
            ContextFrame,
            FinancialSnapshot,
            HealthBaseline,
            HelmScores,
        )

        return ContextFrame(
            user_id="test-user",
            user_name="Mahmoud",
            helm_scores=HelmScores(wealth=60, health=55, time=50),
            financial=FinancialSnapshot(total_balance=10000, currency="AED"),
            health=HealthBaseline(
                sleep_hours_avg=7.5,
                sleep_quality=72,
                steps_avg=8000,
                stress_level=45,
            ),
        )

    def _make_plan(self, template_id):
        from services.intelligence.schemas import ActionPlan

        return ActionPlan(response_template_id=template_id)

    def _make_scores(self, **kwargs):
        from services.intelligence.schemas import ScoreDeltas

        return ScoreDeltas(**kwargs)

    @pytest.mark.asyncio
    async def test_greeting_template(self):
        """Greeting template interpolates user name."""
        gen = self._make_generator()
        plan = self._make_plan("greeting")
        scores = self._make_scores()
        context = self._make_context()
        intent = self._make_intent("greeting")
        resp = await gen.generate(plan, scores, context, intent)

        assert "Mahmoud" in resp.text
        assert resp.generated_by == "template"
        assert resp.template_id == "greeting"
        assert resp.llm_tokens_used == 0

    @pytest.mark.asyncio
    async def test_balance_template(self):
        """Balance template shows currency and amount."""
        gen = self._make_generator()
        plan = self._make_plan("balance_report")
        scores = self._make_scores()
        context = self._make_context()
        intent = self._make_intent("balance_check")
        resp = await gen.generate(plan, scores, context, intent)

        assert "AED" in resp.text
        assert "10,000" in resp.text

    @pytest.mark.asyncio
    async def test_sleep_template(self):
        """Sleep template shows hours and quality."""
        gen = self._make_generator()
        plan = self._make_plan("sleep_report")
        scores = self._make_scores()
        context = self._make_context()
        intent = self._make_intent("sleep_analysis")
        resp = await gen.generate(plan, scores, context, intent)

        assert "7.5" in resp.text
        assert "72" in resp.text

    @pytest.mark.asyncio
    async def test_fallback_response(self):
        """No template and no LLM → safe fallback."""
        gen = self._make_generator()
        plan = self._make_plan(None)
        scores = self._make_scores()
        context = self._make_context()
        intent = self._make_intent("general_conversation")
        resp = await gen.generate(plan, scores, context, intent)

        assert len(resp.text) > 0
        assert resp.generated_by == "fallback"

    @pytest.mark.asyncio
    async def test_tradeoff_context_appended(self):
        """Trade-off context is appended when scores have tradeoff."""
        from services.intelligence.schemas import DimensionDelta

        gen = self._make_generator()
        plan = self._make_plan("ride_booked")
        scores = self._make_scores(
            wealth=DimensionDelta(
                dimension="wealth", delta=-5, direction="down", reasoning="Ride cost"
            ),
            time=DimensionDelta(
                dimension="time", delta=+5, direction="up", reasoning="Time saved"
            ),
            has_tradeoff=True,
        )
        context = self._make_context()
        intent = self._make_intent("mobility_booking")
        resp = await gen.generate(plan, scores, context, intent)

        assert "Trade-off" in resp.text

    def test_local_search_format_is_honest(self):
        """Rendered places show the disclaimer and never bare 'price' as fact."""
        gen = self._make_generator()
        places = [
            {
                "name": "Zabeel Park",
                "address": "Gate 4",
                "price_level": 0,
                "rating": 4.6,
                "distance_text": "1.2 km",
                "duration_text": "15 mins",
            },
            {"name": "Fitness First", "address": "Marina", "price_level": 3},
        ]
        text = gen._format_local_search("yoga studio", places)
        assert "Zabeel Park" in text and "Fitness First" in text
        assert "1.2 km" in text and "Free" in text and "$$$" in text
        # Honest about what the numbers are, and offers the ride hand-off.
        assert "not exact fees" in text
        assert "price a ride" in text

    def test_local_search_fallback_never_fabricates(self):
        """No location → honest fallback, no invented venues/numbers."""
        gen = self._make_generator()
        intent = self._make_intent("local_search")
        text = gen._build_fallback_response(intent, self._make_context())
        assert "share your location" in text or "your area" in text

    # (Wellbeing trade-off logic now lives in the decision engine —
    #  see tests/unit/test_decision_engine.py.)

    @pytest.mark.asyncio
    async def test_local_search_uses_real_places_with_location(self):
        """With location + a (stubbed) live Maps key, real venues are returned."""
        import services.productivity.google_maps_service as maps_mod
        from services.intelligence.schemas import IntentResult

        class _StubMaps:
            api_key = "real"

            async def places_search(self, query, lat, lng, radius_m=6000, limit=5):
                return [
                    {
                        "name": "Zabeel Park",
                        "address": "Gate 4",
                        "price_level": 0,
                        "rating": 4.6,
                        "lat": 25.23,
                        "lng": 55.30,
                    }
                ]

            async def get_distance_matrix(self, origins, destinations, mode="walking"):
                return {
                    "status": "OK",
                    "origin_addresses": ["You"],
                    "destination_addresses": destinations,
                    "rows": [
                        {
                            "elements": [
                                {
                                    "status": "OK",
                                    "distance": {"text": "1.2 km", "value": 1200},
                                    "duration": {"text": "15 mins", "value": 900},
                                }
                            ]
                        }
                    ],
                }

        original = maps_mod.get_google_maps_service
        maps_mod.get_google_maps_service = lambda: _StubMaps()
        try:
            gen = self._make_generator()
            intent = IntentResult(
                intent="local_search",
                confidence=0.85,
                original_text="find some near me",
                entities={"resolved_topic": "yoga studio"},
                request_location={"lat": 25.2, "lng": 55.27},
            )
            resp = await gen.generate(
                self._make_plan(None), self._make_scores(), self._make_context(), intent
            )
        finally:
            maps_mod.get_google_maps_service = original

        assert resp.generated_by == "maps"
        assert "Zabeel Park" in resp.text
        assert "1.2 km" in resp.text
        assert len(resp.data["places"]) == 1


# ============================================================================
# Schema Tests
# ============================================================================


class TestSchemas:
    """Tests for pipeline schema contracts."""

    def test_input_envelope_defaults(self):
        from services.intelligence.schemas import InputEnvelope

        envelope = InputEnvelope(user_id="u1", raw_text="hi", normalized_text="hi")
        assert envelope.user_id == "u1"
        assert envelope.locale == "en"
        assert len(envelope.request_id) > 0

    def test_context_frame_defaults(self):
        from services.intelligence.schemas import ContextFrame

        ctx = ContextFrame(user_id="u1")
        assert ctx.helm_scores.wealth == 50.0
        assert ctx.crisis_mode is False

    def test_score_deltas_serialization(self):
        """ScoreDeltas serializes cleanly to JSON."""
        from services.intelligence.schemas import ScoreDeltas

        scores = ScoreDeltas()
        data = scores.model_dump()
        json_str = json.dumps(data, default=str)
        assert len(json_str) > 0

    def test_pipeline_result_structure(self):
        from services.intelligence.schemas import (
            PipelineResult,
            ResponseEnvelope,
            PipelineTrace,
        )

        result = PipelineResult(
            response=ResponseEnvelope(text="Hello"),
            trace=PipelineTrace(user_id="u1"),
        )
        assert result.response.text == "Hello"
        assert result.tier == 0

    def test_request_tier_enum(self):
        from services.intelligence.schemas import RequestTier

        assert RequestTier.TIER_0 == 0
        assert RequestTier.TIER_3 == 3


# ============================================================================
# Intent Taxonomy Registry Tests
# ============================================================================


class TestTaxonomyRegistry:
    """Tests for the intent taxonomy registry."""

    def test_registry_has_expected_count(self):
        """Registry has at least 40 intents."""
        from services.intelligence.intent_taxonomy import ALL_INTENTS

        assert len(ALL_INTENTS) >= 40

    def test_all_intents_have_name(self):
        from services.intelligence.intent_taxonomy import ALL_INTENTS

        for entry in ALL_INTENTS:
            assert entry.name, f"Intent missing name: {entry}"

    def test_all_intents_have_category(self):
        from services.intelligence.intent_taxonomy import ALL_INTENTS

        valid_categories = {
            "wealth",
            "health",
            "time",
            "mobility",
            "lifestyle",
            "cross_domain",
        }
        for entry in ALL_INTENTS:
            assert (
                entry.category in valid_categories
            ), f"Invalid category: {entry.category}"

    def test_lookup_by_name(self):
        from services.intelligence.intent_taxonomy import get_intent_entry

        entry = get_intent_entry("balance_check")
        assert entry is not None
        assert entry.category == "wealth"

    def test_lookup_nonexistent(self):
        from services.intelligence.intent_taxonomy import get_intent_entry

        entry = get_intent_entry("nonexistent_intent")
        assert entry is None

    def test_get_all_names(self):
        from services.intelligence.intent_taxonomy import get_all_intent_names

        names = get_all_intent_names()
        assert "balance_check" in names
        assert "greeting" in names

    def test_get_by_category(self):
        from services.intelligence.intent_taxonomy import get_intents_by_category

        wealth = get_intents_by_category("wealth")
        assert len(wealth) >= 10

    def test_no_duplicate_names(self):
        from services.intelligence.intent_taxonomy import ALL_INTENTS

        names = [e.name for e in ALL_INTENTS]
        assert len(names) == len(set(names)), "Duplicate intent names found"
