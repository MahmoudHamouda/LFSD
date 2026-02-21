"""
Stage 6: Response Generation — Tiered: Templates for Simple, LLM for Nuanced.

Tier 0: Pre-written templates with variable interpolation ("Your balance is {amount}").
Tier 1-2: Lightweight LLM generates personalized response with HELM persona.
Tier 3: Response for heavy-reasoning scenarios (LLM already produced the analysis).

The user never sees raw scores — they see human-readable trade-off language.
Response cap: 250 tokens for standard responses.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from .schemas import (
    ActionPlan,
    ContextFrame,
    IntentResult,
    ResponseEnvelope,
    ScoreDeltas,
)

logger = logging.getLogger("intelligence.response_generator")


# ============================================================================
# Response Template Library
# ============================================================================

RESPONSE_TEMPLATES: Dict[str, str] = {
    # --- Greetings ---
    "greeting": (
        "Hey {user_name}! 👋 I'm here to help you optimize your wealth, health, and time. "
        "What can I do for you?"
    ),
    "clarification_request": (
        "I want to make sure I help you with the right thing. "
        "Could you tell me a bit more about what you're looking for?"
    ),
    "feedback_received": (
        "Thanks for the feedback! I've noted it. "
        "Your input helps me serve you better."
    ),

    # --- Wealth ---
    "balance_report": (
        "Your current balance across all accounts is **{currency} {total_balance:,.2f}**."
    ),
    "spending_report": (
        "Here's your spending summary{period_text}. "
        "Total: **{currency} {total_spent:,.2f}**."
    ),
    "financial_advice": (
        "Based on your financial profile, here's my take on this."
    ),
    "goal_created": (
        "Great goal! I've noted your target of **{currency} {target_amount:,.0f}** "
        "for *{title}*. Let's track your progress."
    ),
    "bill_payment_confirm": (
        "I can schedule that payment for you. "
        "Just confirm and I'll take care of it."
    ),
    "budget_status": (
        "Here's where you stand with your budget this month."
    ),
    "investment_info": (
        "Let me pull up some investment insights for you."
    ),
    "loan_info": (
        "Here's what I can tell you about loan options."
    ),
    "salary_report": (
        "Your income summary is ready."
    ),
    "expense_categorized": (
        "Done — I've updated the category for that expense."
    ),
    "net_worth_report": (
        "Your net worth summary is ready."
    ),
    "cashflow_report": (
        "Here's your income vs. expenses breakdown."
    ),
    "subscription_list": (
        "Here are your active subscriptions and recurring charges."
    ),

    # --- Health ---
    "health_summary": (
        "Here's your health overview, {user_name}."
    ),
    "sleep_report": (
        "Last night you got **{sleep_hours:.1f} hours** of sleep "
        "with a quality score of **{sleep_quality:.0f}/100**."
    ),
    "activity_report": (
        "You've taken **{steps:,} steps** today. Keep it up!"
    ),
    "nutrition_logged": (
        "Logged! Your nutrition entry has been saved."
    ),
    "stress_report": (
        "Your current stress level is at **{stress_level:.0f}/100**. "
        "{stress_advice}"
    ),
    "recovery_report": (
        "Your recovery status: {recovery_text}."
    ),
    "workout_plan": (
        "Here's a workout plan based on your fitness level."
    ),
    "hydration_reminder": (
        "💧 Time to hydrate! Staying hydrated improves focus and energy."
    ),
    "mental_health_report": (
        "Thanks for checking in with yourself — that's a healthy habit."
    ),
    "health_goal_created": (
        "Your health goal *{title}* has been set. Let's make it happen! 💪"
    ),

    # --- Time ---
    "event_scheduled": (
        "Done! *{title}* has been added to your calendar."
    ),
    "calendar_view": (
        "Here's what's coming up on your calendar."
    ),
    "focus_time_blocked": (
        "I've blocked focus time on your calendar. "
        "No interruptions — deep work mode. 🎯"
    ),
    "meeting_scheduled": (
        "Meeting scheduled. I'll send the invite out."
    ),
    "reminder_set": (
        "Reminder set! I'll make sure you don't forget."
    ),
    "time_audit": (
        "Here's how you've been spending your time."
    ),
    "productivity_report": (
        "Your productivity score is **{productivity:.0f}/100**."
    ),
    "commute_options": (
        "Here are your commute options."
    ),

    # --- Mobility ---
    "ride_prices": (
        "Here are the ride options I found."
    ),
    "ride_booked": (
        "Your ride has been booked! 🚗"
    ),
    "ride_cancelled": (
        "Your ride has been cancelled. No cancellation fee was charged."
    ),
    "booking_list": (
        "Here are your current bookings."
    ),
    "car_purchase_analysis": (
        "I've analyzed car options based on your financial profile."
    ),

    # --- Phase 2: New Templates ---
    "subscription_list": (
        "Here are your active subscriptions. "
        "Review them to see if any can be optimized. 💰"
    ),
    "budget_monitor": (
        "Here's your budget status for the month."
    ),
    "salary_insight": (
        "Based on your salary data, here's an income overview."
    ),
    "net_worth_report": (
        "Your estimated net worth summary is ready."
    ),
    "expense_breakdown": (
        "Here's how your expenses break down by category."
    ),
    "hydration_reminder": (
        "Quick reminder: stay hydrated! 💧 Aim for 8 glasses today."
    ),
    "health_overview": (
        "Here's a snapshot of your overall health metrics."
    ),
    "deadline_alert": (
        "Heads-up: you have an upcoming deadline. Stay on track! ⏰"
    ),
    "productivity_insight": (
        "Your productivity score is **{productivity:.0f}/100**. "
        "Here's what stood out."
    ),
    "savings_goal_set": (
        "Great start! Your savings goal has been set. "
        "I'll help you track and stay on target. 🎯"
    ),
}

# Crisis-mode template overrides — softer tone, support-oriented
CRISIS_TEMPLATE_OVERRIDES: Dict[str, str] = {
    "balance_report": (
        "Your current balance is **{currency} {total_balance:,.2f}**. "
        "I know finances can feel tough right now. "
        "Let me know if you'd like help budgeting or finding savings opportunities."
    ),
    "financial_advice": (
        "I understand money matters are stressful right now. "
        "Let me look at this carefully and find the gentlest path forward for you."
    ),
    "spending_report": (
        "Here's your spending summary{period_text}. "
        "Total: **{currency} {total_spent:,.2f}**. "
        "I see some areas where we could save — want me to dig in?"
    ),
}

# Stress advice based on level
_STRESS_ADVICE = {
    "low": "You're doing great — keep up the good work!",
    "medium": "Consider taking short breaks to manage your stress.",
    "high": "Your stress is elevated. Try a 5-minute breathing exercise.",
}


class ResponseGenerator:
    """
    Stage 6 of the HELM Intelligence Pipeline.

    Generates the user-facing response using templates (Tier 0)
    or lightweight LLM (Tier 1–2) with HELM's persona.
    """

    def __init__(self, llm_model=None, llm_api_key: Optional[str] = None):
        """
        Args:
            llm_model: Lightweight LLM model for personalized responses.
            llm_api_key: API key (to check mock mode).
        """
        self.llm_model = llm_model
        self.llm_api_key = llm_api_key

    async def generate(
        self,
        action_plan: ActionPlan,
        scores: ScoreDeltas,
        context: ContextFrame,
        intent: IntentResult,
    ) -> ResponseEnvelope:
        """
        Generate user-facing response.

        Tier 0: Template interpolation.
        Tier 1-2: LLM with HELM persona.
        Tier 3: LLM already handled in synthesis — just format.
        """
        template_id = action_plan.response_template_id

        # --- Template path (Tier 0) ---
        if template_id and template_id in RESPONSE_TEMPLATES:
            # Check for crisis-mode override
            if context.crisis_mode and template_id in CRISIS_TEMPLATE_OVERRIDES:
                text = self._interpolate_template(
                    template_id, context, intent, scores,
                    template_override=CRISIS_TEMPLATE_OVERRIDES[template_id],
                )
                logger.info("Using crisis-mode template override for '%s'", template_id)
            else:
                text = self._interpolate_template(template_id, context, intent, scores)
            text = self._append_score_context(text, scores, context)

            return ResponseEnvelope(
                text=text,
                response_type=self._infer_response_type(intent.intent),
                data=self._build_response_data(intent, context),
                generated_by="template",
                template_id=template_id,
            )

        # --- LLM path (Tier 1-3) ---
        if self.llm_model and self.llm_api_key != "mock":
            return await self._generate_with_llm(action_plan, scores, context, intent)

        # --- Fallback ---
        return ResponseEnvelope(
            text=self._build_fallback_response(intent, context),
            response_type="text",
            generated_by="fallback",
        )

    # ------------------------------------------------------------------
    # Template Interpolation
    # ------------------------------------------------------------------

    def _interpolate_template(
        self,
        template_id: str,
        context: ContextFrame,
        intent: IntentResult,
        scores: ScoreDeltas,
        template_override: Optional[str] = None,
    ) -> str:
        """Interpolate a template with context and entity values."""
        template = template_override or RESPONSE_TEMPLATES.get(template_id, "")

        # Build variable dict
        variables = {
            "user_name": context.user_name,
            "currency": context.financial.currency,
            "total_balance": context.financial.total_balance,
            "total_spent": intent.entities.get("total_spent", 0),
            "target_amount": intent.entities.get("target_amount", 0),
            "title": intent.entities.get("title", "your goal"),
            "sleep_hours": context.health.sleep_hours_avg,
            "sleep_quality": context.health.sleep_quality,
            "steps": context.health.steps_avg,
            "stress_level": context.health.stress_level,
            "productivity": context.time.productivity_score,
            "period_text": f" for {intent.entities['time_period']}" if intent.entities.get("time_period") else "",
            "stress_advice": self._get_stress_advice(context.health.stress_level),
            "recovery_text": "Looking good" if (context.health.hrv_avg or 50) > 40 else "Take it easy today",
        }

        try:
            return template.format(**variables)
        except (KeyError, ValueError) as e:
            logger.warning("Template interpolation failed for '%s': %s", template_id, e)
            return template  # Return raw template if interpolation fails

    def _append_score_context(
        self, text: str, scores: ScoreDeltas, context: ContextFrame
    ) -> str:
        """Append human-readable score context if there are meaningful deltas."""
        parts = []

        if scores.has_tradeoff:
            parts.append("\n\n**Trade-off detected:**")
            if scores.wealth.delta != 0:
                direction = "📈" if scores.wealth.delta > 0 else "📉"
                parts.append(f"- Wealth {direction} {scores.wealth.reasoning}")
            if scores.health.delta != 0:
                direction = "💚" if scores.health.delta > 0 else "💔"
                parts.append(f"- Health {direction} {scores.health.reasoning}")
            if scores.time.delta != 0:
                direction = "⏰" if scores.time.delta > 0 else "⏳"
                parts.append(f"- Time {direction} {scores.time.reasoning}")

            wealth_score = context.helm_scores.wealth
            time_score = context.helm_scores.time
            health_score = context.helm_scores.health
            
            advice = []
            if scores.wealth.delta < 0 and scores.time.delta > 0:
                if wealth_score < 40:
                    advice.append("💡 **HELM Advice:** Since your Wealth index is currently low, you should prioritize less expensive options even if they take more time.")
                elif time_score < 40:
                    advice.append("💡 **HELM Advice:** Since you are currently very short on time, this financial trade-off is recommended to protect your schedule.")
                else:
                    advice.append("💡 **HELM Advice:** Both your Wealth and Time indices are healthy, making this a balanced personal choice.")
            elif scores.time.delta < 0 and scores.wealth.delta > 0:
                if time_score < 40:
                    advice.append("💡 **HELM Advice:** Since your Time index is currently low, you should avoid options that consume excessive time, even if they save money.")
                elif wealth_score < 40:
                    advice.append("💡 **HELM Advice:** Since your Wealth index is currently low, taking extra time to save money is a highly recommended trade-off.")
                else:
                    advice.append("💡 **HELM Advice:** Both your Wealth and Time indices are healthy, making this a balanced personal choice.")
            elif scores.health.delta > 0 and (scores.wealth.delta < 0 or scores.time.delta < 0):
                if health_score < 40:
                    advice.append("💡 **HELM Advice:** Your Health index needs attention. Investing time or money into this health benefit is strongly recommended.")
            
            if advice:
                parts.append("\n" + "\n".join(advice))

        if scores.goal_impacts:
            parts.append("\n**Impact on goals:**")
            for impact in scores.goal_impacts:
                parts.append(f"- {impact}")

        if scores.crisis_override:
            parts.append("\n⚠️ *Note: One of your HELM dimensions is in critical range.*")

        if parts:
            return text + "\n".join(parts)
        return text

    # ------------------------------------------------------------------
    # LLM Response Generation
    # ------------------------------------------------------------------

    async def _generate_with_llm(
        self,
        action_plan: ActionPlan,
        scores: ScoreDeltas,
        context: ContextFrame,
        intent: IntentResult,
    ) -> ResponseEnvelope:
        """Generate personalized response via lightweight LLM."""
        try:
            import asyncio

            prompt = self._build_response_prompt(action_plan, scores, context, intent)

            response = await asyncio.to_thread(
                self.llm_model.generate_content,
                prompt,
            )

            text = response.text.strip()
            tokens_est = (len(prompt) + len(text)) // 4

            logger.info("LLM response generated (tokens~%d)", tokens_est)

            return ResponseEnvelope(
                text=text,
                response_type=self._infer_response_type(intent.intent),
                data=self._build_response_data(intent, context),
                generated_by="llm",
                llm_tokens_used=tokens_est,
            )

        except Exception as e:
            logger.error("LLM response generation failed: %s", e)
            return ResponseEnvelope(
                text=self._build_fallback_response(intent, context),
                response_type="text",
                generated_by="fallback",
            )

    def _build_response_prompt(
        self,
        action_plan: ActionPlan,
        scores: ScoreDeltas,
        context: ContextFrame,
        intent: IntentResult,
    ) -> str:
        """Build persona-aware prompt for response generation. Target: <300 tokens input."""
        score_summary = (
            f"W:{scores.wealth.delta:+.0f} H:{scores.health.delta:+.0f} T:{scores.time.delta:+.0f} "
            f"(net:{scores.net_impact})"
        )

        return f"""You are HELM, a personal life optimization assistant.
Tone: warm, direct, not overly mathematical. Never show raw scores to the user.
Respond in under 250 tokens.

User: {context.user_name}
Scores: Wealth={context.helm_scores.wealth:.0f} Health={context.helm_scores.health:.0f} Time={context.helm_scores.time:.0f}
Impact: {score_summary}
Goals affected: {scores.goal_impacts[:2] if scores.goal_impacts else "None"}
Crisis: {context.crisis_mode}

User asked: "{intent.original_text}"
Intent: {intent.intent}
Entities: {json.dumps(intent.entities, default=str)}

Generate a helpful, personalized response. If there are trade-offs, explain them in plain language.
Do NOT mention scores, deltas, or policies. Speak like a trusted advisor."""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _infer_response_type(self, intent: str) -> str:
        """Map intent to response type for frontend rendering."""
        type_map = {
            "spending_report": "financial_report",
            "balance_check": "financial_balance",
            "cashflow_report": "financial_report",
            "mobility_price_check": "mobility_options",
            "mobility_booking": "mobility_booking_confirmed",
            "mobility_cancellation": "mobility_cancellation_confirmed",
            "car_purchase": "car_purchase_analysis",
            "get_bookings": "booking_list",
        }
        return type_map.get(intent, "text")

    def _build_response_data(
        self, intent: IntentResult, context: ContextFrame
    ) -> Dict[str, Any]:
        """Build structured data payload for frontend rendering."""
        data: Dict[str, Any] = {}

        if intent.intent == "balance_check":
            data = {
                "total_balance": context.financial.total_balance,
                "currency": context.financial.currency,
            }
        elif intent.intent in ("spending_report", "cashflow_report"):
            data = {
                "period": intent.entities.get("time_period", "this month"),
                "category": intent.entities.get("category", "all"),
            }

        return data

    def _build_fallback_response(
        self, intent: IntentResult, context: ContextFrame
    ) -> str:
        """Build a safe fallback response when templates and LLM fail."""
        return (
            f"I understand you're asking about {intent.intent.replace('_', ' ')}. "
            f"Let me look into this for you, {context.user_name}."
        )

    def _get_stress_advice(self, stress_level: float) -> str:
        """Get appropriate stress advice based on level."""
        if stress_level < 40:
            return _STRESS_ADVICE["low"]
        elif stress_level < 70:
            return _STRESS_ADVICE["medium"]
        return _STRESS_ADVICE["high"]
