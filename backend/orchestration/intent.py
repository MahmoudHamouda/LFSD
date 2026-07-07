import json
import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class Intent(BaseModel):
    name: str
    confidence: float
    entities: Dict[str, Any]
    required_entities_present: bool


class IntentClassifier:
    """
    Deterministic intent classifier.
    Routes user input into canonical intents:
    MOBILITY, FINANCE, HEALTH, PRODUCTIVITY, LIFESTYLE, GENERAL
    """

    INTENTS = {
        "MOBILITY": {"required": ["destination"]},
        "FINANCE": {"required": []},
        "HEALTH": {"required": []},
        "PRODUCTIVITY": {"required": []},
        "LIFESTYLE": {"required": []},
        "GENERAL": {"required": []},
    }

    # Whole-word mobility triggers. Matched with \b boundaries so common words
    # like "good", "ago", "category" don't accidentally trigger a ride flow.
    MOBILITY_KEYWORDS = [
        "go",
        "going",
        "ride",
        "rides",
        "airport",
        "hotel",
        "taxi",
        "cab",
        "uber",
        "careem",
        "drive",
        "driving",
        "commute",
        "book",
    ]

    # Short affirmations / answers that indicate the user is continuing a
    # pending clarification (e.g. answering "where are you coming from?").
    CONTINUATION_PHRASES = {
        "yes",
        "yeah",
        "yep",
        "yup",
        "sure",
        "ok",
        "okay",
        "please",
        "correct",
        "right",
        "now",
        "current location",
        "use current location",
        "from current location",
        "my current location",
    }

    # Keywords that clearly belong to another vertical — if the current message
    # contains one of these it is a fresh request, not a mobility continuation.
    _OTHER_INTENT_KEYWORDS = [
        "spend",
        "budget",
        "afford",
        "balance",
        "buy",
        "invest",
        "save",
        "weather",
        "eat",
        "sleep",
        "workout",
        "exercise",
        "meeting",
        "schedule",
        "calendar",
        "weight",
        "steps",
    ]

    # Wellbeing/exercise activities. "Should I go out to run, walk or do yoga?"
    # is a wellbeing question, not a ride request — even though it contains
    # "go" + "to". Only an EXPLICIT ride token overrides this guard.
    _ACTIVITY_WORDS = [
        "run",
        "running",
        "jog",
        "jogging",
        "walk",
        "walking",
        "yoga",
        "swim",
        "swimming",
        "workout",
        "exercise",
        "hike",
        "hiking",
        "gym",
        "stroll",
        "stretch",
        "meditate",
        "pilates",
        "cycle",
        "cycling",
    ]
    # Explicit ride tokens (NOT "book" — "book a yoga class" is not a ride).
    _EXPLICIT_RIDE_RE = re.compile(
        r"\b(uber|careem|taxi|cab|ride|rides)\b", re.IGNORECASE
    )

    def _has_mobility_signal(self, text: str) -> bool:
        """True when a message independently expresses a ride/commute request."""
        text_lower = (text or "").lower()

        # Activity/wellbeing phrasing ("go out to run", "walk or do yoga") is not
        # a ride request unless an explicit ride token (uber/taxi/ride/…) is
        # present. This prevents "go" + "to" from hijacking wellbeing questions.
        if not self._EXPLICIT_RIDE_RE.search(text_lower):
            if any(
                re.search(rf"\b{re.escape(w)}\b", text_lower)
                for w in self._ACTIVITY_WORDS
            ):
                return False

        is_mobility = any(
            re.search(rf"\b{re.escape(k)}\b", text_lower)
            for k in self.MOBILITY_KEYWORDS
        )
        has_direction = bool(re.search(r"\b(to|from)\b", text_lower))
        is_explicit_booking = bool(re.search(r"\b(book|uber|careem)\b", text_lower))
        return is_mobility and (has_direction or is_explicit_booking)

    def _looks_like_continuation(self, text: str) -> bool:
        """
        True when a message reads like an answer to a pending mobility
        clarification (a short place/time reply or an affirmation) rather than a
        brand-new question on another topic.
        """
        t = (text or "").lower().strip(" .!?")
        if t in self.CONTINUATION_PHRASES:
            return True
        words = t.split()
        if len(words) <= 4 and "?" not in text:
            if not any(k in t for k in self._OTHER_INTENT_KEYWORDS):
                return True
        return False

    def _extract_mobility_entities(self, text: str) -> Dict[str, str]:
        text_lower = text.lower()
        entities = {}

        # Origin extraction: 'from <place>'
        org_match = re.search(
            r"\bfrom\s+([a-zA-Z0-9\s]+?)(?=\bto\b|\band\b|,|\.|\?|!|$|\bi\b|\bwe\b|\bhe\b|\bshe\b|\bit\b|\bthey\b)",
            text_lower,
        )
        if org_match:
            entities["origin"] = org_match.group(1).strip()

        # Destination extraction: 'to <place>'
        dest_match = re.search(
            r"\bto\s+([a-zA-Z0-9\s]+?)(?=\bfrom\b|\band\b|,|\.|\?|!|$|\bi\b|\bwe\b|\bhe\b|\bshe\b|\bit\b|\bthey\b|\bleave\b|\bgo\b|\bdepart\b|\barrive\b)",
            text_lower,
        )
        if dest_match:
            dest = dest_match.group(1).strip()
            # Ignore common verbs that follow 'to'
            if dest and dest not in ["leave", "go", "depart", "arrive", "book", "get"]:
                entities["destination"] = dest

        return entities

    def classify(self, text: str, history: List[Dict[str, Any]] = None) -> Intent:
        """Determines the intent from text with confidence."""
        text_lower = text.lower()

        # 1. Mobility Check — does THIS message express a ride request?
        has_mobility_signal = self._has_mobility_signal(text)

        # Only treat the message as a mobility continuation when the user is
        # plausibly answering a pending clarification. Critically, we scan only
        # prior USER messages for real mobility intent — never the assistant's
        # own clarification text (which contains "going?"/"destination" and
        # would otherwise trap every following message in the ride flow).
        recent_mobility_context = False
        if history and not has_mobility_signal and self._looks_like_continuation(text):
            for msg in reversed(history[-6:]):
                if not isinstance(msg, dict) or msg.get("role") != "user":
                    continue
                if self._has_mobility_signal(msg.get("content", "")):
                    recent_mobility_context = True
                    break

        if has_mobility_signal or recent_mobility_context:
            entities = self._extract_mobility_entities(text)

            # Determine if this is an explicit execution command
            is_action_verb = any(
                v in text_lower for v in ["book ", "reserve", "order", "book it"]
            )
            if is_action_verb:
                entities["action"] = "book"

            # Context-aware entity filling (look back for missing origin/destination)
            if history:
                for msg in reversed(history[-10:]):
                    if isinstance(msg, dict) and msg.get("role") == "user":
                        past_entities = self._extract_mobility_entities(
                            msg.get("content", "")
                        )
                        if (
                            "destination" not in entities
                            and "destination" in past_entities
                        ):
                            entities["destination"] = past_entities["destination"]
                        if "origin" not in entities and "origin" in past_entities:
                            entities["origin"] = past_entities["origin"]

            has_req = all(
                req in entities for req in self.INTENTS["MOBILITY"]["required"]
            )

            # Additional heuristic: If "airport" is requested, make sure we got a destination
            if "airport" in text_lower and "destination" not in entities:
                entities["destination"] = "airport"
                has_req = True

            # Additional heuristic: if booking is explicitly mentioned without a destination,
            # we capture the intent but flag it as missing required entities so the Orchestrator
            # can prompt the user normally instead of dropping to the LLM.
            if ("book" in text_lower or "uber" in text_lower) and not has_req:
                # It's definitely a mobility intent, but we need more info.
                return Intent(
                    name="MOBILITY",
                    confidence=0.8,
                    entities=entities,
                    required_entities_present=False,
                )

            return Intent(
                name="MOBILITY",
                confidence=0.9 if has_req else 0.6,
                entities=entities,
                required_entities_present=has_req,
            )

        # Add other deterministic checks here
        finance_keywords = ["spend", "budget", "afford", "balance", "buy"]
        if any(k in text_lower for k in finance_keywords):
            return Intent(
                name="FINANCE",
                confidence=0.8,
                entities={},
                required_entities_present=True,
            )

        return Intent(
            name="GENERAL", confidence=1.0, entities={}, required_entities_present=True
        )
