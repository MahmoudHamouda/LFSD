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
        "GENERAL": {"required": []}
    }

    def _extract_mobility_entities(self, text: str) -> Dict[str, str]:
        text_lower = text.lower()
        entities = {}
        
        # Origin extraction: 'from <place>'
        org_match = re.search(r'\bfrom\s+([a-zA-Z0-9\s]+?)(?=\bto\b|\band\b|,|\.|\?|!|$|\bi\b|\bwe\b|\bhe\b|\bshe\b|\bit\b|\bthey\b)', text_lower)
        if org_match:
            entities["origin"] = org_match.group(1).strip()
            
        # Destination extraction: 'to <place>'
        dest_match = re.search(r'\bto\s+([a-zA-Z0-9\s]+?)(?=\bfrom\b|\band\b|,|\.|\?|!|$|\bi\b|\bwe\b|\bhe\b|\bshe\b|\bit\b|\bthey\b|\bleave\b|\bgo\b|\bdepart\b|\barrive\b)', text_lower)
        if dest_match:
            dest = dest_match.group(1).strip()
            # Ignore common verbs that follow 'to'
            if dest and dest not in ["leave", "go", "depart", "arrive", "book", "get"]:
                entities["destination"] = dest
                
        return entities

    def classify(self, text: str, history: List[Dict[str, Any]] = None) -> Intent:
        """Determines the intent from text with confidence."""
        text_lower = text.lower()
        
        # 1. Mobility Check
        mobility_keywords = ['go', 'ride', 'airport', 'hotel', 'taxi', 'uber', 'careem', 'drive', 'commute', 'book']
        is_mobility = any(keyword in text_lower for keyword in mobility_keywords)
        has_direction = ('to ' in text_lower or 'from ' in text_lower)
        is_explicit_booking = ('book ' in text_lower or 'uber' in text_lower or 'careem' in text_lower)
        
        # Check history to see if we were just discussing mobility
        recent_mobility_context = False
        if history and not is_mobility:
            # If the user says "yes" or similar, check if the assistant just asked a mobility question
            for msg in reversed(history[-3:]):
                content = msg.get("content", "") if isinstance(msg, dict) else str(msg)
                if any(keyword in content.lower() for keyword in ['ride', 'uber', 'careem', 'destination', 'going?']):
                    recent_mobility_context = True
                    break
        
        if (is_mobility and (has_direction or is_explicit_booking)) or (recent_mobility_context and is_explicit_booking):
            entities = self._extract_mobility_entities(text)
            
            # Context-aware entity filling (look back for missing origin/destination)
            if history:
                for msg in reversed(history[-10:]):
                    if isinstance(msg, dict) and msg.get("role") == "user":
                        past_entities = self._extract_mobility_entities(msg.get("content", ""))
                        if "destination" not in entities and "destination" in past_entities:
                            entities["destination"] = past_entities["destination"]
                        if "origin" not in entities and "origin" in past_entities:
                            entities["origin"] = past_entities["origin"]

            has_req = all(req in entities for req in self.INTENTS["MOBILITY"]["required"])
            
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
                     required_entities_present=False
                 )
                 
            return Intent(
                name="MOBILITY",
                confidence=0.9 if has_req else 0.6,
                entities=entities,
                required_entities_present=has_req
            )
            
        # Add other deterministic checks here
        finance_keywords = ['spend', 'budget', 'afford', 'balance', 'buy']
        if any(k in text_lower for k in finance_keywords):
            return Intent(name="FINANCE", confidence=0.8, entities={}, required_entities_present=True)

        return Intent(
            name="GENERAL",
            confidence=1.0,
            entities={},
            required_entities_present=True
        )
