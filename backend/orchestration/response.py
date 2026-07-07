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

    @staticmethod
    def _ride_handoff_links(deeplinks: Dict[str, str]) -> str:
        """Render pre-filled hand-off links (Uber + universal Maps directions)."""
        parts = []
        if deeplinks.get("uber"):
            parts.append(f"🚗 [Open in Uber →]({deeplinks['uber']})")
        if deeplinks.get("maps"):
            parts.append(f"🗺️ [Directions / other apps →]({deeplinks['maps']})")
        return "  •  ".join(parts) if parts else ""

    def _format_mobility_response(
        self, data: Dict[str, Any], context: Dict[str, Any]
    ) -> str:
        if data.get("error"):
            return data.get(
                "message",
                "An unknown error occurred while communicating with mobility providers.",
            )

        deeplinks = data.get("deeplinks") or {}

        if data.get("status") == "booked":
            origin = data.get("origin", "your location").title()
            destination = data.get("destination", "your destination").title()
            rec = data.get("recommended_option", {})
            label = rec.get("label", "ride")
            cost = rec.get("estimated_cost", 0) or 0
            low = label.lower()

            # Driving yourself isn't a booking at all — don't invent a fare/pickup.
            if "drive" in low or "self" in low or "own car" in low:
                msg = (
                    f"You'd be driving yourself from **{origin}** to "
                    f"**{destination}** — no booking needed."
                )
                if deeplinks.get("maps"):
                    msg += f" [Open directions →]({deeplinks['maps']})"
                msg += (
                    "\n\nWant me to compare ride options (Uber / Careem / taxi) "
                    "instead?"
                )
                return msg

            # Real provider hand-off. We have no live ride-booking integration
            # (Uber/Careem retired their public booking APIs), so we never
            # fabricate a driver — we deep-link into the real app instead.
            cta = self._ride_handoff_links(deeplinks)
            return (
                f"Here's your **{label}** from **{origin}** to **{destination}** — "
                f"estimated fare **AED {cost:.0f}**.\n\n"
                "⚠️ I can't place a live ride booking from inside HELM yet, so this "
                "isn't a confirmed reservation — tap to book it for real:\n"
                f"{cta}"
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

        # Call-to-action: hand off to the real apps via pre-filled deep links.
        if deeplinks.get("uber") or deeplinks.get("maps"):
            lines.append("Ready to go? Tap to book in the app:")
            lines.append(self._ride_handoff_links(deeplinks))
        elif any(a["is_available"] for a in data.get("actions", [])):
            lines.append(
                "Would you like me to compare these further, "
                "or shall I pull up directions?"
            )

        response = "\n".join(lines)
        logger.info(
            f"Composed Response for {origin}->{destination}: len={len(response)}"
        )
        return response
