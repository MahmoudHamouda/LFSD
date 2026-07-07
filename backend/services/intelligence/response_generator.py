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
import re
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
    "financial_advice": ("Based on your financial profile, here's my take on this."),
    "goal_created": (
        "Great goal! I've noted your target of **{currency} {target_amount:,.0f}** "
        "for *{title}*. Let's track your progress."
    ),
    "bill_payment_confirm": (
        "I can schedule that payment for you. " "Just confirm and I'll take care of it."
    ),
    "budget_status": ("Here's where you stand with your budget this month."),
    "investment_info": ("Let me pull up some investment insights for you."),
    "loan_info": ("Here's what I can tell you about loan options."),
    "salary_report": ("Your income summary is ready."),
    "expense_categorized": ("Done — I've updated the category for that expense."),
    "net_worth_report": ("Your net worth summary is ready."),
    "cashflow_report": ("Here's your income vs. expenses breakdown."),
    "subscription_list": ("Here are your active subscriptions and recurring charges."),
    # --- Health ---
    "health_summary": ("Here's your health overview, {user_name}."),
    "sleep_report": (
        "Last night you got **{sleep_hours:.1f} hours** of sleep "
        "with a quality score of **{sleep_quality:.0f}/100**."
    ),
    "activity_report": ("You've taken **{steps:,} steps** today. Keep it up!"),
    "nutrition_logged": ("Logged! Your nutrition entry has been saved."),
    "stress_report": (
        "Your current stress level is at **{stress_level:.0f}/100**. " "{stress_advice}"
    ),
    "recovery_report": ("Your recovery status: {recovery_text}."),
    "workout_plan": ("Here's a workout plan based on your fitness level."),
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
    "event_scheduled": ("Done! *{title}* has been added to your calendar."),
    "calendar_view": ("Here's what's coming up on your calendar."),
    "focus_time_blocked": (
        "I've blocked focus time on your calendar. "
        "No interruptions — deep work mode. 🎯"
    ),
    "meeting_scheduled": ("Meeting scheduled. I'll send the invite out."),
    "reminder_set": ("Reminder set! I'll make sure you don't forget."),
    "time_audit": ("Here's how you've been spending your time."),
    "productivity_report": ("Your productivity score is **{productivity:.0f}/100**."),
    "commute_options": ("Here are your commute options."),
    # --- Mobility ---
    "ride_prices": ("Here are the ride options I found."),
    "ride_booked": ("Your ride has been booked! 🚗"),
    "ride_cancelled": (
        "Your ride has been cancelled. No cancellation fee was charged."
    ),
    "booking_list": ("Here are your current bookings."),
    "car_purchase_analysis": (
        "I've analyzed car options based on your financial profile."
    ),
    # --- Phase 2: New Templates ---
    "subscription_list": (
        "Here are your active subscriptions. "
        "Review them to see if any can be optimized. 💰"
    ),
    "budget_monitor": ("Here's your budget status for the month."),
    "salary_insight": ("Based on your salary data, here's an income overview."),
    "net_worth_report": ("Your estimated net worth summary is ready."),
    "expense_breakdown": ("Here's how your expenses break down by category."),
    "hydration_reminder": (
        "Quick reminder: stay hydrated! 💧 Aim for 8 glasses today."
    ),
    "health_overview": ("Here's a snapshot of your overall health metrics."),
    "deadline_alert": ("Heads-up: you have an upcoming deadline. Stay on track! ⏰"),
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


# ============================================================================
# Wellbeing activity model (for grounded "run vs walk vs yoga" trade-offs)
# ============================================================================
# Values are typical, honest defaults — NOT fabricated precision. time_min is a
# typical session length; cost is a category (outdoor/home = free vs a
# studio/pool/gym fee). The benefit fields are 0-1 relative weights.

_ACTIVITY_PROFILES: Dict[str, Dict[str, Any]] = {
    "run": {
        "label": "Running",
        "time_min": 30,
        "cost": "Free (outdoors)",
        "free": True,
        "cardio": 0.9,
        "strength": 0.3,
        "flexibility": 0.1,
        "stress_relief": 0.5,
        "intensity": 0.9,
        "low_impact": False,
        "best_for": "cardio & endurance",
    },
    "jog": {
        "label": "Jogging",
        "time_min": 30,
        "cost": "Free (outdoors)",
        "free": True,
        "cardio": 0.7,
        "strength": 0.3,
        "flexibility": 0.1,
        "stress_relief": 0.6,
        "intensity": 0.7,
        "low_impact": False,
        "best_for": "a moderate cardio boost",
    },
    "walk": {
        "label": "Walking",
        "time_min": 30,
        "cost": "Free (outdoors)",
        "free": True,
        "cardio": 0.4,
        "strength": 0.2,
        "flexibility": 0.1,
        "stress_relief": 0.8,
        "intensity": 0.3,
        "low_impact": True,
        "best_for": "low-impact movement & de-stressing",
    },
    "yoga": {
        "label": "Yoga",
        "time_min": 45,
        "cost": "Free at home (studio fees vary)",
        "free": True,
        "cardio": 0.2,
        "strength": 0.5,
        "flexibility": 0.9,
        "stress_relief": 0.9,
        "intensity": 0.4,
        "low_impact": True,
        "best_for": "flexibility, strength & calm",
    },
    "swim": {
        "label": "Swimming",
        "time_min": 45,
        "cost": "Pool fee",
        "free": False,
        "cardio": 0.8,
        "strength": 0.6,
        "flexibility": 0.4,
        "stress_relief": 0.6,
        "intensity": 0.7,
        "low_impact": True,
        "best_for": "full-body, low-impact cardio",
    },
    "gym": {
        "label": "Gym workout",
        "time_min": 60,
        "cost": "Membership",
        "free": False,
        "cardio": 0.6,
        "strength": 0.9,
        "flexibility": 0.2,
        "stress_relief": 0.4,
        "intensity": 0.8,
        "low_impact": False,
        "best_for": "building strength",
    },
    "cycle": {
        "label": "Cycling",
        "time_min": 45,
        "cost": "Free (own bike)",
        "free": True,
        "cardio": 0.8,
        "strength": 0.4,
        "flexibility": 0.1,
        "stress_relief": 0.6,
        "intensity": 0.7,
        "low_impact": True,
        "best_for": "low-impact cardio",
    },
}

# Message words → activity key.
_ACTIVITY_ALIASES: Dict[str, str] = {
    "run": "run",
    "running": "run",
    "jog": "jog",
    "jogging": "jog",
    "walk": "walk",
    "walking": "walk",
    "stroll": "walk",
    "yoga": "yoga",
    "swim": "swim",
    "swimming": "swim",
    "gym": "gym",
    "workout": "gym",
    "cycle": "cycle",
    "cycling": "cycle",
    "bike": "cycle",
    "biking": "cycle",
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

        # --- Location-aware local search (real places, honest about numbers) ---
        if intent.intent == "local_search":
            return await self._generate_local_search(scores, context, intent)

        # --- Grounded wellbeing trade-off (run vs walk vs yoga, using scores) ---
        if intent.intent in ("tradeoff_analysis", "general_conversation"):
            options = self._detect_activities(
                f"{intent.original_text} {intent.conversation_context}"
            )
            if len(options) >= 2:
                return self._generate_wellbeing_tradeoff(context, options)

        # --- Template path (Tier 0) ---
        if template_id and template_id in RESPONSE_TEMPLATES:
            # Check for crisis-mode override
            if context.crisis_mode and template_id in CRISIS_TEMPLATE_OVERRIDES:
                text = self._interpolate_template(
                    template_id,
                    context,
                    intent,
                    scores,
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
            "period_text": (
                f" for {intent.entities['time_period']}"
                if intent.entities.get("time_period")
                else ""
            ),
            "stress_advice": self._get_stress_advice(context.health.stress_level),
            "recovery_text": (
                "Looking good"
                if (context.health.hrv_avg or 50) > 40
                else "Take it easy today"
            ),
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
                    advice.append(
                        "💡 **HELM Advice:** Since your Wealth index is currently low, you should prioritize less expensive options even if they take more time."
                    )
                elif time_score < 40:
                    advice.append(
                        "💡 **HELM Advice:** Since you are currently very short on time, this financial trade-off is recommended to protect your schedule."
                    )
                else:
                    advice.append(
                        "💡 **HELM Advice:** Both your Wealth and Time indices are healthy, making this a balanced personal choice."
                    )
            elif scores.time.delta < 0 and scores.wealth.delta > 0:
                if time_score < 40:
                    advice.append(
                        "💡 **HELM Advice:** Since your Time index is currently low, you should avoid options that consume excessive time, even if they save money."
                    )
                elif wealth_score < 40:
                    advice.append(
                        "💡 **HELM Advice:** Since your Wealth index is currently low, taking extra time to save money is a highly recommended trade-off."
                    )
                else:
                    advice.append(
                        "💡 **HELM Advice:** Both your Wealth and Time indices are healthy, making this a balanced personal choice."
                    )
            elif scores.health.delta > 0 and (
                scores.wealth.delta < 0 or scores.time.delta < 0
            ):
                if health_score < 40:
                    advice.append(
                        "💡 **HELM Advice:** Your Health index needs attention. Investing time or money into this health benefit is strongly recommended."
                    )

            if advice:
                parts.append("\n" + "\n".join(advice))

        if scores.goal_impacts:
            parts.append("\n**Impact on goals:**")
            for impact in scores.goal_impacts:
                parts.append(f"- {impact}")

        if scores.crisis_override:
            parts.append(
                "\n⚠️ *Note: One of your HELM dimensions is in critical range.*"
            )

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

        context_block = intent.conversation_context or "(no prior conversation)"

        # Intent-specific guidance appended to the base persona prompt.
        intent_guidance = (
            "Generate a helpful, personalized response. If there are trade-offs, "
            "explain them in plain language."
        )
        if intent.intent == "local_search":
            # Honest fulfilment: we have no live venue-data source, so never
            # invent distances or prices. Resolve what the user is looking for
            # from CONTEXT, suggest concrete place TYPES, and offer next steps.
            intent_guidance = (
                "The user wants to find places near them. Use CONTEXT to resolve "
                "vague references (e.g. 'some' -> the activities just discussed). "
                "Suggest 2-4 concrete TYPES of places that fit, tailored to their "
                "goals. CRITICAL: you do NOT have a live map/venue data source - do "
                "NOT invent specific venue names, distances, or prices. Instead ask "
                "for their area (or to share location), and offer that you can price "
                "a ride to any specific place they choose. If the choice involves a "
                "wealth/health/time trade-off, note it briefly."
            )

        return f"""You are HELM, a personal life optimization assistant.
Tone: warm, direct, not overly mathematical. Never show raw scores to the user.
Respond in under 250 tokens.

User: {context.user_name}
Scores: Wealth={context.helm_scores.wealth:.0f} Health={context.helm_scores.health:.0f} Time={context.helm_scores.time:.0f}
Impact: {score_summary}
Goals affected: {scores.goal_impacts[:2] if scores.goal_impacts else "None"}
Crisis: {context.crisis_mode}

CONTEXT (recent conversation, for resolving what the user means):
{context_block}

User asked: "{intent.original_text}"
Intent: {intent.intent}
Entities: {json.dumps(intent.entities, default=str)}

{intent_guidance}

HONESTY ABOUT LIMITS: If the user asks for something you genuinely cannot
access — live weather, news, sports scores, stock quotes, or any real-time or
external data you have no integration for — say so plainly and briefly (e.g. "I
don't have a live weather connection, so I can't check that"). Do NOT pretend,
and do NOT deflect by talking about your "focus" or "what matters most." State
the limit first, then offer what you genuinely can help with.

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

    # ------------------------------------------------------------------
    # Local search (real places via Google Maps; honest about "numbers")
    # ------------------------------------------------------------------

    # Fallback keyword → Maps search-term map, used only when no LLM is available
    # to extract the topic. Ordered; first matches win.
    _ACTIVITY_PLACE_MAP = (
        (("yoga",), "yoga studio"),
        (("run", "running", "jog", "jogging"), "running track"),
        (("walk", "walking", "hike", "hiking", "stroll"), "park walking trail"),
        (("gym", "workout", "exercise", "fitness", "strength"), "gym"),
        (("swim", "swimming", "pool"), "swimming pool"),
        (("coffee", "cafe", "café"), "cafe"),
        (("eat", "restaurant", "dining", "dinner", "lunch", "food"), "restaurant"),
        (("cowork", "coworking", "study", "focus"), "coworking space"),
    )

    async def _generate_local_search(
        self,
        scores: ScoreDeltas,
        context: ContextFrame,
        intent: IntentResult,
    ) -> ResponseEnvelope:
        """
        Answer "find X near me / how far / how much" with REAL places.

        Uses the user's browser location + Google Places. If either the location
        or a live Maps key is missing, falls back to an honest prompt for the
        user's area — it never fabricates venues, distances, or prices.
        """
        loc = intent.request_location
        query = await self._resolve_place_query(intent)

        if not loc or not query:
            return ResponseEnvelope(
                text=self._build_fallback_response(intent, context),
                response_type="local_search",
                generated_by="fallback",
            )

        places = None
        try:
            from services.productivity.google_maps_service import (
                get_google_maps_service,
            )

            svc = get_google_maps_service()
            places = await svc.places_search(
                query, loc["lat"], loc["lng"], radius_m=6000, limit=5
            )
            if places:
                await self._attach_walking_distances(svc, loc, places)
        except Exception as e:  # never fabricate on failure
            logger.error("local_search lookup failed: %s", e)
            places = None

        if not places:
            return ResponseEnvelope(
                text=self._build_fallback_response(intent, context),
                response_type="local_search",
                generated_by="fallback",
            )

        return ResponseEnvelope(
            text=self._format_local_search(query, places),
            response_type="local_search_results",
            data={"query": query, "places": places},
            generated_by="maps",
        )

    async def _resolve_place_query(self, intent: IntentResult) -> str:
        """Determine what kind of place to search for (resolving referents)."""
        resolved = (intent.entities or {}).get("resolved_topic")
        if isinstance(resolved, str) and resolved.strip():
            return resolved.strip()[:60]

        # Prefer an LLM extraction (best at resolving "some" → the real topic).
        if self.llm_model and self.llm_api_key != "mock":
            try:
                import asyncio

                prompt = (
                    "From this conversation, output a short (2-4 word) Google Maps "
                    "search term for the kind of place the user wants near them. "
                    "Output ONLY the term.\n\n"
                    f"Context:\n{intent.conversation_context or '(none)'}\n"
                    f"User: {intent.original_text}\nSearch term:"
                )
                resp = await asyncio.to_thread(self.llm_model.generate_content, prompt)
                term = (getattr(resp, "text", "") or "").strip()
                term = term.splitlines()[0].strip("\"'.` ")[:60] if term else ""
                if term:
                    return term
            except Exception as e:
                logger.warning("place-query extraction failed: %s", e)

        # Heuristic fallback from the conversation topic.
        blob = f"{intent.conversation_context} {intent.original_text}".lower()
        terms = []
        for keys, term in self._ACTIVITY_PLACE_MAP:
            if any(k in blob for k in keys):
                terms.append(term)
        return " ".join(terms[:3]) if terms else ""

    async def _attach_walking_distances(self, svc, loc, places) -> None:
        """Attach real walking distance/ETA to each place (best-effort)."""
        indexed = [
            (i, p)
            for i, p in enumerate(places)
            if p.get("lat") is not None and p.get("lng") is not None
        ]
        if not indexed:
            return
        dests = [f"{p['lat']},{p['lng']}" for _, p in indexed]
        try:
            matrix = await svc.get_distance_matrix(
                origins=[f"{loc['lat']},{loc['lng']}"],
                destinations=dests,
                mode="walking",
            )
        except Exception:
            return
        if not matrix or matrix.get("status") != "OK":
            return
        # Guard against the service's mock mode (should not occur here, since
        # real place results imply a live key, but stay defensive).
        if any("MOCK" in a for a in matrix.get("origin_addresses", [])):
            return
        rows = matrix.get("rows") or []
        elements = rows[0].get("elements") if rows else []
        for (_, place), el in zip(indexed, elements or []):
            if el.get("status") == "OK":
                place["distance_text"] = (el.get("distance") or {}).get("text")
                place["duration_text"] = (el.get("duration") or {}).get("text")

    def _format_local_search(self, query: str, places: list) -> str:
        """Render real places as markdown — honest about what the numbers are."""
        lines = [f"Here are some **{query}** options near you:\n"]
        for p in places:
            bits = []
            if p.get("distance_text"):
                walk = f" ({p['duration_text']} walk)" if p.get("duration_text") else ""
                bits.append(f"{p['distance_text']} away{walk}")
            if p.get("rating"):
                bits.append(f"⭐ {p['rating']}")
            pl = p.get("price_level")
            if isinstance(pl, int):
                bits.append("Free" if pl == 0 else "$" * pl)
            detail = " · ".join(bits)
            line = f"- **{p.get('name')}**"
            if detail:
                line += f" — {detail}"
            if p.get("address"):
                line += f"\n  {p['address']}"
            lines.append(line)
        lines.append(
            "\n_Distances are walking estimates from Google Maps; any price shown "
            "is Google's $–$$$$ guide, not exact fees._"
        )
        lines.append("Want me to price a ride to any of these?")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Wellbeing trade-off (grounded in the user's scores + health state)
    # ------------------------------------------------------------------

    def _detect_activities(self, text: str) -> list:
        """Return the distinct known activity keys mentioned, in first-seen order."""
        blob = (text or "").lower()
        seen = []
        for word, key in _ACTIVITY_ALIASES.items():
            if re.search(rf"\b{re.escape(word)}\b", blob) and key not in seen:
                # keep first-seen order by position of the word
                seen.append((blob.find(word), key))
        return [k for _, k in sorted(seen)]

    def _generate_wellbeing_tradeoff(
        self, context: ContextFrame, options: list
    ) -> ResponseEnvelope:
        """
        Recommend among run/walk/yoga/… grounded in the user's HELM scores,
        the time each takes, its cost, and their current health state.
        Deterministic and honest — the recommendation traces to real signals.
        """
        h = context.helm_scores.health
        t = context.helm_scores.time
        w = context.helm_scores.wealth
        stress = context.health.stress_level
        activity = context.health.activity_level
        recovery = context.health.hrv_avg if context.health.hrv_avg else 50.0

        signals = {
            "time_poor": t < 50,
            "stressed": stress >= 55,
            "low_activity": activity < 50 or h < 50,
            "low_recovery": recovery < 40,
            "wealth_low": w < 45,
        }

        def suitability(key: str) -> float:
            p = _ACTIVITY_PROFILES[key]
            s = p["cardio"] * 0.5 + p["strength"] * 0.3 + p["flexibility"] * 0.2
            if signals["low_activity"]:
                s += p["cardio"] * 0.6
            if signals["stressed"]:
                s += p["stress_relief"] * 0.9
            elif stress >= 40:
                s += p["stress_relief"] * 0.4
            if signals["time_poor"]:
                s += (60 - p["time_min"]) / 60 * 0.7  # shorter → better
            if signals["low_recovery"]:
                s += 0.5 if p["low_impact"] else -0.3
                s -= p["intensity"] * 0.4
            if signals["wealth_low"] and p["free"]:
                s += 0.3
            return s

        ranked = sorted(options, key=suitability, reverse=True)
        winner = ranked[0]
        wp = _ACTIVITY_PROFILES[winner]

        # Build a grounded reason from the signals the winner satisfies.
        reasons = []
        if signals["stressed"] and wp["stress_relief"] >= 0.7:
            reasons.append(
                f"your stress is elevated ({stress:.0f}/100) and {wp['label'].lower()} "
                "is one of the calmest options"
            )
        if signals["time_poor"]:
            reasons.append(
                f"you're short on time (Time {t:.0f}/100) and it fits in ~{wp['time_min']} min"
            )
        if signals["low_activity"] and wp["cardio"] >= 0.7:
            reasons.append(
                "your recent activity is on the low side, so the cardio boost helps most"
            )
        if signals["low_recovery"] and wp["low_impact"]:
            reasons.append(
                "your recovery is low, so a gentle, low-impact session protects it"
            )
        if signals["wealth_low"] and wp["free"]:
            reasons.append("it's free, which fits your budget right now")
        if not reasons:
            reasons.append(
                "your Health, Time and Wealth are all in good shape, so this is the "
                "best all-round benefit for the time it takes"
            )

        lines = [
            f"Here's how they stack up for **you** right now "
            f"— Health {h:.0f}/100, Time {t:.0f}/100, stress {stress:.0f}/100:\n"
        ]
        for key in options:
            p = _ACTIVITY_PROFILES[key]
            lines.append(
                f"- **{p['label']}** — ~{p['time_min']} min · {p['cost']} · {p['best_for']}"
            )
        lines.append(
            f"\n**My pick: {wp['label']}.** Because " + "; ".join(reasons) + "."
        )
        lines.append(
            "\n_Times are typical session lengths; costs are outdoor/home (free) vs "
            "studio/pool/gym fees — I don't have live class prices. Want me to find "
            "options near you?_"
        )

        return ResponseEnvelope(
            text="\n".join(lines),
            response_type="wellbeing_tradeoff",
            data={
                "recommended": winner,
                "options": options,
                "signals": {k: bool(v) for k, v in signals.items()},
            },
            generated_by="wellbeing_engine",
        )

    def _build_fallback_response(
        self, intent: IntentResult, context: ContextFrame
    ) -> str:
        """Build a safe fallback response when templates and LLM fail."""
        if intent.intent == "local_search":
            # Honest even without an LLM: never fabricate venues/distances/prices.
            return (
                "I can help you find good spots for that. I can't pull live "
                "distances or prices for venues yet — tell me your area (or share "
                "your location) and I'll suggest options. If you pick a specific "
                "place, I can price a ride there for you."
            )
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
