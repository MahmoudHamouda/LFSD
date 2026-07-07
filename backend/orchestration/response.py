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
            origin = data.get("origin", "your location").title()
            destination = data.get("destination", "your destination").title()
            rec = data.get("recommended_option", {})
            label = rec.get("label", "ride")
            cost = rec.get("estimated_cost", 0) or 0
            low = label.lower()

            # Driving yourself isn't a booking at all — don't invent a fare/pickup.
            if "drive" in low or "self" in low or "own car" in low:
                return (
                    f"You'd be driving yourself from **{origin}** to "
                    f"**{destination}** — no booking needed. Want directions, or "
                    "should I compare ride options (Uber / Careem / taxi) instead?"
                )

            # Real provider hand-off. We do NOT have a live ride-booking
            # integration (Uber/Careem retired their public booking APIs), so we
            # never fabricate a driver or claim a real reservation.
            if "uber" in low:
                app = "the **Uber** app"
            elif "careem" in low:
                app = "the **Careem** app"
            elif "taxi" in low or "rta" in low:
                app = (
                    "the **Careem** or **S'hail (RTA)** app, or hail one on the street"
                )
            else:
                app = "the provider's app"

            return (
                f"Here's your **{label}** from **{origin}** to **{destination}** — "
                f"estimated fare **AED {cost:.0f}**.\n\n"
                "⚠️ I can't place a live ride booking from inside HELM yet, so this "
                f"isn't a confirmed reservation. Book it for real in {app}. Want me "
                "to keep comparing options meanwhile?"
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
            f"   *{data.get('rationale', '')}*\n"
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
