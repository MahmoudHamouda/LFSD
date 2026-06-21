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

    async def compose(
        self, intent: str, tool_data: Dict[str, Any], context: Dict[str, Any]
    ) -> str:
        """Produce a short human answer based on tool data."""
        if intent == "MOBILITY":
            return self._format_mobility_response(tool_data, context)
        return "I have received your request, but do not have a composer configuration for it."

    def _format_mobility_response(
        self, data: Dict[str, Any], context: Dict[str, Any]
    ) -> str:
        if data.get("error"):
            return data.get(
                "message",
                "An unknown error occurred while communicating with mobility providers.",
            )

        if data.get("status") == "booked":
            details = data.get("booking_details", {})
            origin = data.get("origin", "your location")
            destination = data.get("destination", "your destination")
            rec = data.get("recommended_option", {})
            return (
                f"✅ **Ride Booked!**\n\n"
                f"Your {rec.get('label', 'ride')} is on the way to take you from **{origin.title()}** to **{destination.title()}**.\n\n"
                f"🚘 **Driver:** {details.get('driver_name', 'System')} ({details.get('car_model', 'Sedan')} - {details.get('license_plate', 'XXX')})\n"
                f"⏱ **Arriving in:** {details.get('pickup_eta_mins', 5)} minutes\n"
                f"💰 **Estimated Fare:** AED {rec.get('estimated_cost', 0):.0f}"
            )

        origin = data.get("origin", "your location")
        destination = data.get("destination", "your destination")
        distance_km = data.get("distance_km", 0)
        rec = data.get("recommended_option")
        options = data.get("options", [])

        if not rec:
            return f"I couldn't find a viable route from {origin} to {destination}."

        # ---- Build response ----
        lines = [
            f"🗺️ **{origin.title()}** → **{destination.title()}** ({distance_km} km)\n",
        ]

        # Recommended
        rec_label = rec.get("label") or rec["mode"].replace("_", " ").title()
        lines.append(
            f"⭐ **Recommended: {rec_label}**  \n"
            f"   ⏱ {rec['eta_minutes']} min  •  💰 AED {rec['estimated_cost']:.0f}  \n"
            f"   _{data.get('rationale', '')}_\n"
        )

        # Alternatives
        alts = [o for o in options if o["mode"] != rec["mode"]]
        if alts:
            lines.append("**Other options:**")
            for o in alts:
                label = o.get("label") or o["mode"].replace("_", " ").title()
                lines.append(
                    f"  • **{label}** — {o['eta_minutes']} min, AED {o['estimated_cost']:.0f}"
                )
            lines.append("")

        # Call-to-action
        if any(a["is_available"] for a in data.get("actions", [])):
            lines.append(
                "Would you like me to **book a ride** for you? "
                'Just say *"yes, book it"* or choose a different option.'
            )

        response = "\n".join(lines)
        logger.info(
            f"Composed Response for {origin}->{destination}: len={len(response)}"
        )
        return response
