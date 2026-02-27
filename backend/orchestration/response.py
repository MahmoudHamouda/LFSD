import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("orchestration.response")

class ResponseComposer:
    """
    LLM-last Response Composer.
    Formats deterministic tool data into a human-friendly response.
    Only uses LLM if necessary to "phrase" the answer.
    """
    def __init__(self, llm_service=None):
        self.llm = llm_service

    async def compose(self, intent: str, tool_data: Dict[str, Any], context: Dict[str, Any]) -> str:
        """
        Produce a short human answer based on tool data.
        """
        if intent == "MOBILITY":
             return self._format_mobility_response(tool_data, context)
        
        return "I have received your request, but do not have a composer configuration for it."

    def _format_mobility_response(self, data: Dict[str, Any], context: Dict[str, Any]) -> str:
        if data.get("error"):
            return data.get("message", "An unknown error occurred while communicating with mobility providers.")
            
        origin = data.get("origin", "your location")
        destination = data.get("destination", "your destination")
        rec = data.get("recommended_option")
        options = data.get("options", [])
        
        if not rec:
             return f"I couldn't find a viable route from {origin} to {destination}."
             
        # Find an alternative
        alt = None
        for o in options:
             if o["mode"] != rec["mode"]:
                  alt = o
                  break
                  
        response = f"To go from **{origin}** to **{destination}**, I recommend **{rec['mode']}** " \
                   f"({rec['eta_minutes']} mins, AED {rec['estimated_cost']}).\n" \
                   f"*{data.get('rationale', 'This fits your profile.')}*\n\n"
                   
        if alt:
             response += f"**Alternative:** {alt['mode']} ({alt['eta_minutes']} mins, AED {alt['estimated_cost']}).\n\n"
             
        # Ask for confirmation
        if any(a["is_available"] for a in data.get("actions", [])):
             response += f"Would you like me to book {rec['mode']} for you? Please confirm to proceed with payment."
        else:
             response += "No direct booking integration is available yet."
             
        # Write to structured log instead of LLM stringification
        logger.info(f"Composed Response for {origin}->{destination}: {response}")
        
        return response
