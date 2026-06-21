"""
Stage 3: Intent Classification — Tiered: Deterministic First, LLM Fallback.

Pass 1 (Deterministic): Decision tree + regex/keyword matching against IntentTaxonomy.
    Resolves ~40-50% of requests. Zero cost, sub-millisecond.

Pass 2 (LLM Fallback): Lightweight Gemini Flash call with structured JSON output.
    Token budget: < 500 tokens total (input + output).

Returns IntentResult with confidence, tier classification, and extracted entities.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from .intent_taxonomy import (
    INTENT_REGISTRY,
    get_all_intent_names,
    get_intent_entry,
    match_deterministic,
)
from .schemas import ContextFrame, InputEnvelope, IntentResult, RequestTier

logger = logging.getLogger("intelligence.intent_classifier")

# Intent types that map from legacy GeminiService intent names
_LEGACY_INTENT_MAP = {
    "financial_report": "spending_report",
    "financial_spend": "spending_report",
    "financial_balance": "balance_check",
    "financial_advisory": "financial_advisory",
    "set_goal": "set_savings_goal",
    "health_report": "health_report",
    "schedule_event": "schedule_event",
    "mobility_price_check": "mobility_price_check",
    "mobility_booking": "mobility_booking",
    "mobility_cancellation": "mobility_cancellation",
    "get_bookings": "get_bookings",
    "mobility.car_purchase": "car_purchase",
    "tradeoff_analysis": "tradeoff_analysis",
    "general_conversation": "general_conversation",
    "needs_clarification": "needs_clarification",
}


class IntentClassifier:
    """
    Stage 3 of the HELM Intelligence Pipeline.

    Two-pass classification:
        1. Deterministic: keywords + regex (free, fast)
        2. LLM fallback: structured JSON classification (lightweight model)
    """

    def __init__(self, llm_model=None, llm_api_key: Optional[str] = None):
        """
        Args:
            llm_model: Configured generative model for fallback classification.
                       If None, deterministic-only mode.
            llm_api_key: API key (used to check if mock mode).
        """
        self.llm_model = llm_model
        self.llm_api_key = llm_api_key

    async def classify(
        self,
        envelope: InputEnvelope,
        context: ContextFrame,
    ) -> IntentResult:
        """
        Classify user intent. Deterministic first, LLM fallback.

        Args:
            envelope: Normalized input from Stage 1.
            context: Assembled context from Stage 2.

        Returns:
            IntentResult with intent name, confidence, tier, and entities.
        """
        text = envelope.normalized_text

        # ------------------------------------------------------------------
        # Pass 1: Deterministic Classification
        # ------------------------------------------------------------------
        match = match_deterministic(text)
        if match is not None:
            intent_name, confidence, match_type = match
            entry = get_intent_entry(intent_name)

            logger.info(
                "Deterministic classification: %s (confidence=%.2f, match=%s)",
                intent_name,
                confidence,
                match_type,
            )

            return IntentResult(
                intent=intent_name,
                confidence=confidence,
                dimensions=list(entry.dimensions) if entry else [],
                tier=RequestTier(entry.default_tier) if entry else RequestTier.TIER_1,
                entities=self._extract_entities_deterministic(text, intent_name),
                classified_by="deterministic",
                original_text=envelope.raw_text,
                llm_tokens_used=0,
            )

        # ------------------------------------------------------------------
        # Pass 2: LLM Fallback
        # ------------------------------------------------------------------
        if self.llm_model is None or self.llm_api_key == "mock":
            logger.info("No LLM available — defaulting to general_conversation")
            return IntentResult(
                intent="general_conversation",
                confidence=0.5,
                dimensions=[],
                tier=RequestTier.TIER_1,
                classified_by="deterministic_fallback",
                original_text=envelope.raw_text,
            )

        return await self._classify_with_llm(envelope, context)

    # ------------------------------------------------------------------
    # LLM Classification
    # ------------------------------------------------------------------

    async def _classify_with_llm(
        self,
        envelope: InputEnvelope,
        context: ContextFrame,
    ) -> IntentResult:
        """Call lightweight LLM for intent classification. Token budget: <500."""
        try:
            import asyncio

            all_intents = get_all_intent_names()

            # Build compact prompt (minimizing tokens)
            prompt = self._build_classification_prompt(
                envelope.normalized_text,
                envelope.conversation_history[-3:],  # Last 3 messages only
                all_intents,
            )

            response = await asyncio.to_thread(
                self.llm_model.generate_content,
                prompt,
                generation_config={"response_mime_type": "application/json"},
            )

            # Parse structured response
            response_text = response.text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:-3]
            elif response_text.startswith("```"):
                response_text = response_text[3:-3]

            data = json.loads(response_text)
            if not isinstance(data, dict):
                data = {"intent": "general_conversation", "confidence": 0.5}

            intent_name = data.get("intent", "general_conversation")

            # Map legacy intents if the LLM returns old names
            intent_name = _LEGACY_INTENT_MAP.get(intent_name, intent_name)

            entry = get_intent_entry(intent_name)
            confidence = float(data.get("confidence", 0.7))

            # Determine tier
            if entry:
                tier = RequestTier(entry.default_tier)
                dimensions = list(entry.dimensions)
            else:
                tier = RequestTier.TIER_1
                dimensions = []

            # Escalation: if confidence < 0.7, bump tier to at least TIER_2
            if confidence < 0.7 and tier.value < 2:
                tier = RequestTier.TIER_2

            # Extract entities from LLM response
            entities = {}
            if "entities" in data and isinstance(data["entities"], dict):
                entities = data["entities"]
            else:
                # Flatten top-level entity-like keys
                skip_keys = {"intent", "confidence", "original_text"}
                entities = {k: v for k, v in data.items() if k not in skip_keys}

            # Estimate tokens used (rough: input + output chars / 4)
            tokens_est = (len(prompt) + len(response_text)) // 4

            logger.info(
                "LLM classification: %s (confidence=%.2f, tier=%d, tokens~%d)",
                intent_name,
                confidence,
                tier.value,
                tokens_est,
            )

            return IntentResult(
                intent=intent_name,
                confidence=confidence,
                dimensions=dimensions,
                tier=tier,
                entities=entities,
                classified_by="llm",
                original_text=envelope.raw_text,
                llm_tokens_used=tokens_est,
            )

        except Exception as e:
            logger.error("LLM classification failed: %s — falling back", e)
            return IntentResult(
                intent="general_conversation",
                confidence=0.4,
                dimensions=[],
                tier=RequestTier.TIER_1,
                classified_by="llm_fallback_error",
                original_text=envelope.raw_text,
            )

    def _build_classification_prompt(
        self,
        text: str,
        history: List[Dict[str, str]],
        all_intents: List[str],
    ) -> str:
        """Build a compact classification prompt. Target: <300 input tokens."""
        history_str = ""
        if history:
            recent = history[-3:]
            for msg in recent:
                role = "U" if msg.get("role") == "user" else "A"
                content = msg.get("content", "")[:100]
                history_str += f"{role}: {content}\n"

        intent_list = ", ".join(all_intents)

        return f"""Classify the user message into one intent. Return JSON only.

INTENTS: [{intent_list}]

RULES:
- "Can I afford X?" → financial_advisory
- "How much did I spend?" → spending_report  
- "Should I X or Y?" → tradeoff_analysis
- Ambiguous across domains → needs_clarification
- Greetings/social → greeting

History:
{history_str}
User: "{text}"

Return: {{"intent": "...", "confidence": 0.0-1.0, "entities": {{}}}}"""

    # ------------------------------------------------------------------
    # Deterministic Entity Extraction
    # ------------------------------------------------------------------

    def _extract_entities_deterministic(
        self, text: str, intent_name: str
    ) -> Dict[str, Any]:
        """
        Extract entities from text using regex for known intent types.
        """
        import re

        entities: Dict[str, Any] = {}
        text_lower = text.lower()

        # Money amounts
        money_match = re.search(
            r"(?:aed|usd|\$|£|€)\s*[\d,]+\.?\d*|[\d,]+\.?\d*\s*(?:aed|usd|dollars?)",
            text_lower,
        )
        if money_match:
            amount_str = re.sub(r"[^\d.]", "", money_match.group())
            try:
                entities["amount"] = float(amount_str)
            except ValueError:
                pass

        # Locations (for mobility intents)
        if intent_name.startswith("mobility_") or intent_name == "commute_planning":
            from_to = re.search(r"from\s+(.+?)\s+to\s+(.+)", text_lower)
            to_from = re.search(r"to\s+(.+?)\s+from\s+(.+)", text_lower)
            if from_to:
                entities["start_location"] = from_to.group(1).strip()
                entities["destination"] = from_to.group(2).strip()
            elif to_from:
                entities["destination"] = to_from.group(1).strip()
                entities["start_location"] = to_from.group(2).strip()
            else:
                to_only = re.search(r"to\s+([^,\s.?!]+(?:\s+[^,\s.?!]+)*)", text_lower)
                if to_only:
                    entities["destination"] = to_only.group(1).strip()

        # Time periods
        time_match = re.search(
            r"(?:this|last|past)\s+(?:week|month|year|quarter)", text_lower
        )
        if time_match:
            entities["time_period"] = time_match.group()

        # Categories (for spending)
        if intent_name in ("spending_report", "expense_categorize"):
            categories = [
                "food",
                "transport",
                "rent",
                "utilities",
                "entertainment",
                "shopping",
                "health",
                "education",
                "travel",
                "groceries",
                "dining",
                "fuel",
                "insurance",
            ]
            for cat in categories:
                if cat in text_lower:
                    entities["category"] = cat
                    break

        return entities
