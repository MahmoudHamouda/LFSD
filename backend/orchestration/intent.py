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
        
        # Try to extract "from X to Y" or "to Y from X"
        from_to_match = re.search(r'from\s+(.+?)\s+to\s+(.+)', text_lower)
        to_from_match = re.search(r'to\s+(.+?)\s+from\s+(.+)', text_lower)
        
        if from_to_match:
            entities["origin"] = from_to_match.group(1).strip()
            entities["destination"] = from_to_match.group(2).strip()
        elif to_from_match:
            entities["destination"] = to_from_match.group(1).strip()
            entities["origin"] = to_from_match.group(2).strip()
        else:
            # Try just "to Y"
            to_match = re.search(r'to\s+([^, .?!]+(?:\s+[^, .?!]+)*)', text_lower)
            if to_match and any(word in text_lower for word in ['go', 'ride', 'airport', 'hotel', 'drive', 'book']):
                entities["destination"] = to_match.group(1).strip()
                
        return entities

    def classify(self, text: str) -> Intent:
        """Determines the intent from text with confidence."""
        text_lower = text.lower()
        
        # 1. Mobility Check
        mobility_keywords = ['go', 'ride', 'airport', 'hotel', 'taxi', 'uber', 'careem', 'drive', 'commute']
        if any(keyword in text_lower for keyword in mobility_keywords) and ('to ' in text_lower or 'from ' in text_lower):
            entities = self._extract_mobility_entities(text)
            has_req = all(req in entities for req in self.INTENTS["MOBILITY"]["required"])
            
            # Additional heuristic: If "airport" is requested, make sure we got a destination
            if "airport" in text_lower and "destination" not in entities:
                 entities["destination"] = "airport"
                 has_req = True
                 
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
