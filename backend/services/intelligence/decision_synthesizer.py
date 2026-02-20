"""
Stage 5: Decision Synthesis — Deterministic with Optional LLM Escalation.

Maps intent + score profile → predefined ActionPlan template.
Escalates to heavy LLM only when:
    - Intent confidence < 0.7
    - Score deltas are contradictory across dimensions
    - User explicitly asks for deep analysis

Target: < 15% of requests escalate to heavy LLM.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from .schemas import (
    ActionPlan,
    ActionStep,
    ActionType,
    ContextFrame,
    IntentResult,
    RequestTier,
    ScoreDeltas,
)

logger = logging.getLogger("intelligence.decision_synthesizer")


# ============================================================================
# Action Template Registry
# ============================================================================

# Maps intent → ActionPlan template. For Tier 0/1 requests, these templates
# are used directly without LLM involvement.

ACTION_TEMPLATES: Dict[str, Dict[str, Any]] = {
    # --- Wealth ---
    "balance_check": {
        "response_template_id": "balance_report",
        "steps": [{"action_type": "respond_only"}],
    },
    "spending_report": {
        "response_template_id": "spending_report",
        "steps": [{"action_type": "respond_only"}],
    },
    "financial_advisory": {
        "response_template_id": "financial_advice",
        "steps": [{"action_type": "respond_only"}],
    },
    "set_savings_goal": {
        "response_template_id": "goal_created",
        "steps": [
            {"action_type": "execute_financial", "target_service": "goal_service",
             "requires_confirmation": True},
        ],
    },
    "bill_payment": {
        "response_template_id": "bill_payment_confirm",
        "steps": [
            {"action_type": "execute_financial", "target_service": "billing_service",
             "requires_confirmation": True},
        ],
    },
    "budget_alert": {
        "response_template_id": "budget_status",
        "steps": [{"action_type": "respond_only"}],
    },
    "investment_query": {
        "response_template_id": "investment_info",
        "steps": [{"action_type": "respond_only"}],
    },
    "loan_inquiry": {
        "response_template_id": "loan_info",
        "steps": [{"action_type": "respond_only"}],
    },
    "salary_analysis": {
        "response_template_id": "salary_report",
        "steps": [{"action_type": "respond_only"}],
    },
    "expense_categorize": {
        "response_template_id": "expense_categorized",
        "steps": [{"action_type": "respond_only"}],
    },
    "net_worth_check": {
        "response_template_id": "net_worth_report",
        "steps": [{"action_type": "respond_only"}],
    },
    "cashflow_report": {
        "response_template_id": "cashflow_report",
        "steps": [{"action_type": "respond_only"}],
    },
    "subscription_review": {
        "response_template_id": "subscription_list",
        "steps": [{"action_type": "respond_only"}],
    },

    # --- Health ---
    "health_report": {
        "response_template_id": "health_summary",
        "steps": [{"action_type": "respond_only"}],
    },
    "sleep_analysis": {
        "response_template_id": "sleep_report",
        "steps": [{"action_type": "respond_only"}],
    },
    "activity_summary": {
        "response_template_id": "activity_report",
        "steps": [{"action_type": "respond_only"}],
    },
    "nutrition_log": {
        "response_template_id": "nutrition_logged",
        "steps": [
            {"action_type": "execute_health", "target_service": "nutrition_service",
             "requires_confirmation": False},
        ],
    },
    "stress_check": {
        "response_template_id": "stress_report",
        "steps": [{"action_type": "respond_only"}],
    },
    "recovery_status": {
        "response_template_id": "recovery_report",
        "steps": [{"action_type": "respond_only"}],
    },
    "workout_plan": {
        "response_template_id": "workout_plan",
        "steps": [{"action_type": "respond_only"}],
    },
    "hydration_reminder": {
        "response_template_id": "hydration_reminder",
        "steps": [{"action_type": "respond_only"}],
    },
    "mental_health_check": {
        "response_template_id": "mental_health_report",
        "steps": [{"action_type": "respond_only"}],
    },
    "health_goal_set": {
        "response_template_id": "health_goal_created",
        "steps": [
            {"action_type": "execute_health", "target_service": "goal_service",
             "requires_confirmation": True},
        ],
    },

    # --- Time ---
    "schedule_event": {
        "response_template_id": "event_scheduled",
        "steps": [
            {"action_type": "execute_calendar", "target_service": "calendar_service",
             "requires_confirmation": True},
        ],
    },
    "calendar_view": {
        "response_template_id": "calendar_view",
        "steps": [{"action_type": "respond_only"}],
    },
    "focus_time_block": {
        "response_template_id": "focus_time_blocked",
        "steps": [
            {"action_type": "execute_calendar", "target_service": "calendar_service",
             "requires_confirmation": False},
        ],
    },
    "meeting_schedule": {
        "response_template_id": "meeting_scheduled",
        "steps": [
            {"action_type": "execute_calendar", "target_service": "calendar_service",
             "requires_confirmation": True},
        ],
    },
    "deadline_reminder": {
        "response_template_id": "reminder_set",
        "steps": [
            {"action_type": "execute_calendar", "target_service": "calendar_service",
             "requires_confirmation": False},
        ],
    },
    "time_audit": {
        "response_template_id": "time_audit",
        "steps": [{"action_type": "respond_only"}],
    },
    "productivity_report": {
        "response_template_id": "productivity_report",
        "steps": [{"action_type": "respond_only"}],
    },
    "commute_planning": {
        "response_template_id": "commute_options",
        "steps": [{"action_type": "respond_only"}],
    },

    # --- Mobility ---
    "mobility_price_check": {
        "response_template_id": "ride_prices",
        "steps": [{"action_type": "respond_only"}],
    },
    "mobility_booking": {
        "response_template_id": "ride_booked",
        "steps": [
            {"action_type": "execute_mobility", "target_service": "mobility_service",
             "requires_confirmation": True},
        ],
    },
    "mobility_cancellation": {
        "response_template_id": "ride_cancelled",
        "steps": [
            {"action_type": "execute_mobility", "target_service": "mobility_service",
             "requires_confirmation": False},
        ],
    },
    "get_bookings": {
        "response_template_id": "booking_list",
        "steps": [{"action_type": "respond_only"}],
    },
    "car_purchase": {
        "response_template_id": "car_purchase_analysis",
        "steps": [{"action_type": "respond_only"}],
    },

    # --- Cross-Domain ---
    "greeting": {
        "response_template_id": "greeting",
        "steps": [{"action_type": "respond_only"}],
    },
    "feedback": {
        "response_template_id": "feedback_received",
        "steps": [{"action_type": "respond_only"}],
    },
    "general_conversation": {
        "response_template_id": None,  # Requires LLM
        "steps": [{"action_type": "respond_only"}],
    },
    "needs_clarification": {
        "response_template_id": "clarification_request",
        "steps": [{"action_type": "respond_only"}],
    },
}

# Intents that always escalate to heavy LLM
_ALWAYS_ESCALATE = {
    "tradeoff_analysis",
    "career_change",
    "relocation_analysis",
    "life_event_planning",
}


class DecisionSynthesizer:
    """
    Stage 5 of the HELM Intelligence Pipeline.

    Maps intent + score profile → ActionPlan.
    Escalates to heavy LLM for genuinely novel scenarios.
    """

    def __init__(self, heavy_llm_model=None, llm_api_key: Optional[str] = None):
        """
        Args:
            heavy_llm_model: Configured heavy model for Tier 3 escalation.
            llm_api_key: API key (to check mock mode).
        """
        self.heavy_llm_model = heavy_llm_model
        self.llm_api_key = llm_api_key

    async def synthesize(
        self,
        intent: IntentResult,
        scores: ScoreDeltas,
        context: ContextFrame,
    ) -> ActionPlan:
        """
        Determine the recommended action(s) for the given intent and scores.

        Most requests resolve via template lookup.
        Novel/ambiguous scenarios escalate to heavy LLM.
        """
        # Check if escalation is needed
        needs_escalation = self._should_escalate(intent, scores)

        if needs_escalation and self.heavy_llm_model and self.llm_api_key != "mock":
            logger.info("Escalating to heavy LLM for intent '%s'", intent.intent)
            return await self._synthesize_with_llm(intent, scores, context)

        # Template-based synthesis
        return self._synthesize_from_template(intent, scores)

    # ------------------------------------------------------------------
    # Template-based synthesis
    # ------------------------------------------------------------------

    def _synthesize_from_template(
        self, intent: IntentResult, scores: ScoreDeltas
    ) -> ActionPlan:
        """Build ActionPlan from template registry."""
        template = ACTION_TEMPLATES.get(intent.intent, ACTION_TEMPLATES["general_conversation"])

        steps = []
        for step_def in template.get("steps", []):
            steps.append(
                ActionStep(
                    action_type=ActionType(step_def.get("action_type", "respond_only")),
                    target_service=step_def.get("target_service"),
                    parameters=intent.entities.copy(),
                    requires_confirmation=step_def.get("requires_confirmation", False),
                )
            )

        plan = ActionPlan(
            steps=steps,
            response_template_id=template.get("response_template_id"),
            response_tone="warm_direct",
            synthesized_by="template",
        )

        logger.info(
            "Template synthesis: intent=%s, template=%s, steps=%d",
            intent.intent,
            plan.response_template_id,
            len(steps),
        )

        return plan

    # ------------------------------------------------------------------
    # LLM-based synthesis (Tier 3)
    # ------------------------------------------------------------------

    async def _synthesize_with_llm(
        self,
        intent: IntentResult,
        scores: ScoreDeltas,
        context: ContextFrame,
    ) -> ActionPlan:
        """Escalate to heavy LLM for novel scenario reasoning."""
        try:
            import asyncio

            prompt = self._build_synthesis_prompt(intent, scores, context)

            response = await asyncio.to_thread(
                self.heavy_llm_model.generate_content,
                prompt,
                generation_config={"response_mime_type": "application/json"},
            )

            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:-3]
            elif response_text.startswith("```"):
                response_text = response_text[3:-3]

            data = json.loads(response_text)
            tokens_est = (len(prompt) + len(response_text)) // 4

            # Build ActionPlan from LLM output
            steps = []
            for step_def in data.get("steps", [{"action_type": "respond_only"}]):
                steps.append(
                    ActionStep(
                        action_type=ActionType(step_def.get("action_type", "respond_only")),
                        target_service=step_def.get("target_service"),
                        parameters=step_def.get("parameters", {}),
                        requires_confirmation=step_def.get("requires_confirmation", True),
                    )
                )

            plan = ActionPlan(
                steps=steps,
                response_template_id=None,
                response_tone=data.get("tone", "warm_direct"),
                synthesized_by="llm",
                llm_tokens_used=tokens_est,
                escalation_reason=self._escalation_reason(intent, scores),
            )

            logger.info(
                "LLM synthesis: intent=%s, tokens~%d, steps=%d",
                intent.intent,
                tokens_est,
                len(steps),
            )
            return plan

        except Exception as e:
            logger.error("LLM synthesis failed: %s — falling back to template", e)
            return self._synthesize_from_template(intent, scores)

    def _build_synthesis_prompt(
        self,
        intent: IntentResult,
        scores: ScoreDeltas,
        context: ContextFrame,
    ) -> str:
        """Build reasoning prompt for heavy LLM. Includes full context and scores."""
        return f"""You are the Decision Synthesizer for HELM, a personal life optimization system.

USER CONTEXT:
- Name: {context.user_name}
- HELM Scores: Wealth={context.helm_scores.wealth:.0f}, Health={context.helm_scores.health:.0f}, Time={context.helm_scores.time:.0f}
- Financial: Income={context.financial.monthly_income:.0f}, Expenses={context.financial.monthly_expenses:.0f}, Balance={context.financial.total_balance:.0f}
- Crisis Mode: {context.crisis_mode} {context.crisis_dimensions}
- Risk Tolerance: {context.risk_tolerance}
- Goals: {json.dumps(context.life_goals[:3], default=str)}

USER REQUEST: "{intent.original_text}"
CLASSIFIED INTENT: {intent.intent} (confidence: {intent.confidence:.2f})
ENTITIES: {json.dumps(intent.entities, default=str)}

SCORE EVALUATION:
- Wealth Impact: {scores.wealth.delta:+.1f} ({scores.wealth.reasoning})
- Health Impact: {scores.health.delta:+.1f} ({scores.health.reasoning})
- Time Impact: {scores.time.delta:+.1f} ({scores.time.reasoning})
- Net: {scores.net_impact}, Tradeoff: {scores.has_tradeoff}
- Goal Impacts: {scores.goal_impacts}

Analyze this scenario and return a JSON ActionPlan:
{{
    "analysis": "2-3 sentence analysis of the tradeoffs",
    "recommendation": "clear recommendation",
    "steps": [{{"action_type": "respond_only", "parameters": {{}}}}],
    "tone": "warm_direct"
}}

Be concise. Focus on the tradeoffs between dimensions. Return ONLY valid JSON."""

    # ------------------------------------------------------------------
    # Escalation logic
    # ------------------------------------------------------------------

    def _should_escalate(self, intent: IntentResult, scores: ScoreDeltas) -> bool:
        """Determine if this request needs heavy LLM reasoning."""
        # Always escalate certain intent types
        if intent.intent in _ALWAYS_ESCALATE:
            return True

        # Escalate if confidence is too low
        if intent.confidence < 0.7:
            return True

        # Escalate if scores are contradictory (mixed impact)
        if scores.has_tradeoff and abs(scores.wealth.delta) > 5 and abs(scores.health.delta) > 5:
            return True

        # Escalate if user explicitly asks for deep analysis
        deep_analysis_keywords = ["help me think", "help me decide", "what should i do", "analyze this"]
        if any(kw in intent.original_text.lower() for kw in deep_analysis_keywords):
            return True

        return False

    def _escalation_reason(self, intent: IntentResult, scores: ScoreDeltas) -> str:
        """Return human-readable reason for escalation."""
        reasons = []
        if intent.intent in _ALWAYS_ESCALATE:
            reasons.append(f"Intent '{intent.intent}' requires deep analysis")
        if intent.confidence < 0.7:
            reasons.append(f"Low intent confidence ({intent.confidence:.2f})")
        if scores.has_tradeoff:
            reasons.append("Contradictory score deltas across dimensions")
        return "; ".join(reasons) if reasons else "Deep analysis requested"
