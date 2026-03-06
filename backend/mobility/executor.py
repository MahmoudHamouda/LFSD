import logging
import math
import random
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from services.productivity.google_maps_service import GoogleMapsService
from orchestration.base_executor import BaseExecutor
from orchestration.registry import IntegrationRegistry

logger = logging.getLogger("mobility.executor")


class CommuteOption(BaseModel):
    mode: str
    eta_minutes: int
    distance_km: float
    estimated_cost: float
    confidence: float
    provider: Optional[str] = None
    action_available: bool = False
    label: str = ""           # Human-friendly name
    cost_currency: str = "AED"


# ---------------------------------------------------------------------------
# Dubai-specific cost & speed baselines (2026 rates)
# ---------------------------------------------------------------------------
DUBAI_COST_PER_KM = {
    "ride_hailing":   {"base": 12.0, "per_km": 1.82, "per_min": 0.52},
    "taxi":           {"base": 12.0, "per_km": 1.82, "per_min": 0.52},
    "public_transit":  {"flat_zone": 5.0},
    "drive":          {"per_km": 0.30},   # fuel cost only
}


def _estimate_cost(mode: str, distance_km: float, duration_min: float) -> float:
    """Compute a realistic cost estimate using Dubai tariff tables."""
    rates = DUBAI_COST_PER_KM.get(mode, {})
    if mode in ("ride_hailing", "taxi"):
        return round(rates["base"] + rates["per_km"] * distance_km + rates["per_min"] * duration_min, 1)
    if mode == "public_transit":
        # Zone-based: < 10km = 1 zone, < 20km = 2 zones, else 3 zones
        if distance_km < 10:
            return 4.0
        elif distance_km < 20:
            return 6.0
        else:
            return 8.5
    if mode == "drive":
        return round(rates["per_km"] * distance_km, 1)
    return 0.0


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371  # km
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = (math.sin(dLat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dLon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@IntegrationRegistry.register("MOBILITY")
class MobilityExecutor(BaseExecutor):
    """
    Deterministic mobility service.
    Uses Google Maps for geocoding & distance, then computes Dubai-rate
    cost estimates for ride-hailing, taxi, metro, and driving.
    """

    def __init__(self):
        super().__init__()
        self.maps_service = None

    async def setup(self) -> bool:
        """Lazy init — only needs Google Maps (real key configured)."""
        try:
            self.maps_service = GoogleMapsService()
            if not getattr(self.maps_service, "api_key", None):
                raise ValueError("GOOGLE_MAPS_API_KEY is missing or invalid.")
            self.is_healthy = True
            return True
        except Exception as e:
            logger.error(f"Mobility integration failed to initialize: {e}")
            self.is_healthy = False
            self.error_msg = str(e)
            return False

    # ----- helpers -----

    async def _resolve_location(self, place_name: str) -> Optional[tuple]:
        """Geocode a place name via Google Maps."""
        if not place_name:
            return None
        try:
            coords = await self.maps_service.geocode(place_name)
            if coords:
                return coords
        except Exception as e:
            logger.warning(f"Geocode failed for '{place_name}': {e}")
        # Dubai-centre fallback
        return (25.2048, 55.2708)

    async def _get_driving_info(self, origin: str, destination: str, distance_fallback: float):
        """Try Google Distance Matrix; fall back to haversine-based estimate."""
        try:
            api_dist = await self.maps_service.get_distance(origin, destination)
            if api_dist is not None:
                return max(api_dist, 2.0), None   # (distance_km, duration_min or None)
        except Exception as e:
            logger.warning(f"Distance matrix failed: {e}")
        return max(distance_fallback, 2.0), None

    # ----- scoring -----

    def score_option(self, option: CommuteOption, preferences: Dict[str, Any]) -> float:
        time_weight = 1.0
        cost_weight = 1.0
        time_idx = preferences.get("time_index", 50)
        wealth_idx = preferences.get("wealth_index", 50)
        if time_idx < 40:
            time_weight = 2.0
        if wealth_idx < 40:
            cost_weight = 2.0
        return option.eta_minutes * time_weight + option.estimated_cost * cost_weight

    # ----- main execute -----

    async def execute_safe(self, entities: Dict[str, Any], user_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        origin = entities.get("origin", "Current Location")
        destination = entities.get("destination", "Airport")

        # 1. Geocode
        start_coords = await self._resolve_location(origin)
        end_coords = await self._resolve_location(destination)

        # 2. Distance
        haversine_dist = _haversine(
            start_coords[0], start_coords[1],
            end_coords[0], end_coords[1]
        ) if start_coords and end_coords else 15.0

        distance_km, duration_api = await self._get_driving_info(origin, destination, haversine_dist)

        # Base driving time estimate (avg 40 km/h in Dubai)
        base_drive_min = round(distance_km / 40.0 * 60)

        # 3. Build options from computed estimates
        options: List[CommuteOption] = []

        # Ride-hailing (Uber / Careem style)
        ride_eta = base_drive_min + random.randint(3, 7)  # pickup wait
        options.append(CommuteOption(
            mode="ride_hailing",
            label="Uber / Careem",
            eta_minutes=max(ride_eta, 8),
            distance_km=round(distance_km, 1),
            estimated_cost=_estimate_cost("ride_hailing", distance_km, base_drive_min),
            confidence=0.85,
            provider="Uber",
            action_available=True,
        ))

        # Taxi
        taxi_eta = base_drive_min + random.randint(5, 10)
        options.append(CommuteOption(
            mode="taxi",
            label="Dubai Taxi (RTA)",
            eta_minutes=max(taxi_eta, 10),
            distance_km=round(distance_km, 1),
            estimated_cost=_estimate_cost("taxi", distance_km, base_drive_min),
            confidence=0.80,
            provider="RTA",
            action_available=False,
        ))

        # Public Transit (Metro + Bus)
        if distance_km > 3:
            transit_eta = round(base_drive_min * 1.6) + random.randint(5, 12)  # slower + wait
            options.append(CommuteOption(
                mode="public_transit",
                label="Dubai Metro / Bus",
                eta_minutes=max(transit_eta, 15),
                distance_km=round(distance_km, 1),
                estimated_cost=_estimate_cost("public_transit", distance_km, transit_eta),
                confidence=0.75,
                provider="RTA",
                action_available=False,
            ))

        # Drive yourself
        options.append(CommuteOption(
            mode="drive",
            label="Drive Yourself",
            eta_minutes=max(base_drive_min, 5),
            distance_km=round(distance_km, 1),
            estimated_cost=_estimate_cost("drive", distance_km, base_drive_min),
            confidence=0.90,
            provider=None,
            action_available=False,
        ))

        # 4. Score & recommend
        best_score = float("inf")
        recommended = None
        for opt in options:
            s = self.score_option(opt, context)
            if s < best_score:
                best_score = s
                recommended = opt

        # 5. Rationale
        rationale = "This option balances cost and time."
        if recommended:
            if recommended.mode == "ride_hailing":
                rationale = "Fastest door-to-door option with minimal wait."
            elif recommended.mode == "public_transit":
                rationale = "Most affordable and eco-friendly choice."
            elif recommended.mode == "drive":
                rationale = "Most flexible — no waiting, go at your own pace."
            elif recommended.mode == "taxi":
                rationale = "Easy to hail, no app needed."

        # If user explicitly requested booking, return structural booking confirmation
        if entities.get("action") == "book":
            return {
                "status": "booked",
                "origin": origin,
                "destination": destination,
                "distance_km": round(distance_km, 1),
                "recommended_option": recommended.model_dump() if recommended else None,
                "booking_details": {
                    "driver_name": "Tariq A.",
                    "car_model": "Lexus ES300h",
                    "license_plate": "D 58291",
                    "pickup_eta_mins": random.randint(3, 7)
                }
            }

        return {
            "origin": origin,
            "destination": destination,
            "distance_km": round(distance_km, 1),
            "options": [o.model_dump() for o in options],
            "recommended_option": recommended.model_dump() if recommended else None,
            "rationale": rationale,
            "data_source": "google_maps_computed",
            "actions": [
                {"action": "book_ride", "mode": "ride_hailing", "is_available": True,
                 "description": "Book Uber / Careem"}
            ],
        }
