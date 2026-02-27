import logging
import random
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from services.productivity.google_maps_service import GoogleMapsService
from services.integrations.uber_service import UberService
from services.mobility.rta_service import RTAService
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

@IntegrationRegistry.register("MOBILITY")
class MobilityExecutor(BaseExecutor):
    """
    Deterministic mobility service. Fetches route options, costs, and ETAs.
    Recommends best commute using scoring function.
    """
    def __init__(self):
        super().__init__()
        self.maps_service = None
        self.uber_service = None
        self.rta_service = None
        self.base_cost_per_km = {
            "ride_hailing": 2.5,  # AED per km
            "taxi": 2.0,
            "public_transit": 0.5,
            "drive": 0.3
        }
        self.base_speed_kmh = {
            "ride_hailing": 40.0,
            "taxi": 40.0,
            "public_transit": 25.0,
            "drive": 40.0
        }

    async def setup(self) -> bool:
        """Lazy init connection to map service."""
        try:
            self.maps_service = GoogleMapsService()
            self.uber_service = UberService()
            self.rta_service = RTAService()
            if not getattr(self.maps_service, "api_key", None):
                 raise ValueError("GOOGLE_MAPS_API_KEY is missing or invalid.")
            self.is_healthy = True
            return True
        except Exception as e:
            logger.error(f"Mobility integration failed to initialize: {e}")
            self.is_healthy = False
            self.error_msg = str(e)
            return False

    async def _resolve_location(self, place_name: str) -> Optional[tuple]:
        """Geocodes a place name if possible, otherwise returns a mock coord."""
        if not place_name:
            return None
        coords = await self.maps_service.geocode(place_name)
        if coords:
            return coords
        logger.warning(f"Could not geocode {place_name}. Using fallback.")
        return (25.2048, 55.2708)  # Dubai default

    def score_option(self, option: CommuteOption, preferences: Dict[str, Any]) -> float:
        """
        Calculates a score for the option based on user preferences.
        Lower is better (cost vs time).
        """
        # Read preferences (wealth_index, time_index, health_index)
        time_weight = 1.0
        cost_weight = 1.0
        
        # If user has low time index, they prioritize speed
        time_idx = preferences.get('time_index', 50)
        wealth_idx = preferences.get('wealth_index', 50)
        
        if time_idx < 40:
             time_weight = 2.0
        if wealth_idx < 40:
             cost_weight = 2.0
             
        # Simple weighted sum of (ETA * weight) + (Cost * weight)
        # Normalize roughly: ETA ranges 10-60m, Cost ranges 5-100 AED
        score = (option.eta_minutes * time_weight) + (option.estimated_cost * cost_weight)
        return score

    async def execute_safe(self, entities: Dict[str, Any], user_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch ETAs, compute costs, return structured commute options + recommendation.
        """
        origin = entities.get("origin", "Current Location")
        destination = entities.get("destination", "Airport")
        
        # Geocode entities
        start_coords = await self._resolve_location(origin)
        end_coords = await self._resolve_location(destination)
        
        # Calculate rough distance/time using Haversine or Google distance matrix.
        import math
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371  # km
            dLat = math.radians(lat2 - lat1)
            dLon = math.radians(lon2 - lon1)
            a = math.sin(dLat/2) * math.sin(dLat/2) + math.cos(math.radians(lat1)) \
                * math.cos(math.radians(lat2)) * math.sin(dLon/2) * math.sin(dLon/2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            return R * c
            
        distance_km = 15.0 # fallback
        if start_coords and end_coords:
            distance_km = haversine(start_coords[0], start_coords[1], end_coords[0], end_coords[1])
            try:
                # Try getting real road distance
                api_dist = await self.maps_service.get_distance(origin, destination)
                if api_dist is not None:
                    distance_km = api_dist
            except Exception as e:
                logger.error(f"Failed to get exact distance matrix: {e}")
            distance_km = max(distance_km, 2.0) # Assume at least 2km to avoid zero

        options = []
        
        # 1. LIVE RIDE HAILING (Uber API)
        if start_coords and end_coords:
            try:
                uber_est = await self.uber_service.get_price_estimates(
                    start_lat=start_coords[0], start_lng=start_coords[1],
                    end_lat=end_coords[0], end_lng=end_coords[1],
                    user_id=user_id
                )
                if uber_est and uber_est.get("success") and uber_est.get("prices"):
                    # Use the first reasonable product (e.g., standard UberX)
                    price = uber_est["prices"][0]
                    # Uber duration is in seconds
                    duration_mins = int(price.get("duration", 0) / 60) + 5 # 5 mins wait
                    cost = price.get("high_estimate", distance_km * self.base_cost_per_km["ride_hailing"])
                    if cost is not None:
                        options.append(CommuteOption(
                            mode="ride_hailing",
                            eta_minutes=max(duration_mins, 10),
                            distance_km=round(price.get("distance", distance_km), 1),
                            estimated_cost=float(cost),
                            confidence=0.95,
                            provider="Uber",
                            action_available=True
                        ))
            except Exception as e:
                logger.error(f"Uber Service failed: {e}")

        # 2. LIVE PUBLIC TRANSIT (RTA API)
        if start_coords and end_coords:
            try:
                rta_est = await self.rta_service.get_price_estimates(
                    start_lat=start_coords[0], start_lng=start_coords[1],
                    end_lat=end_coords[0], end_lng=end_coords[1],
                    user_id=user_id
                )
                if rta_est and rta_est.get("success") and rta_est.get("prices"):
                    price = rta_est["prices"][0]
                    duration_mins = int(price.get("duration", 1200) / 60)
                    cost = price.get("high_estimate", 5.0)
                    if cost is not None:
                        options.append(CommuteOption(
                            mode="public_transit",
                            eta_minutes=max(duration_mins, 15),
                            distance_km=round(price.get("distance", distance_km), 1),
                            estimated_cost=float(cost),
                            confidence=0.95,
                            provider="RTA",
                            action_available=False
                        ))
            except Exception as e:
                logger.error(f"RTA Service failed: {e}")

        # 3. VERIFY SUCCESS & ERROR REPORTING
        if not options:
            return {
                "error": True,
                "message": (
                    "I am currently unable to fetch live mobility data. The connection to Uber, RTA, or Google Maps "
                    "might be unavailable, or your API quota may have been exceeded. "
                    "Please check your API dashboard and upgrade your plan, or try again later."
                )
            }
        # Compute recommended option
        best_score = float('inf')
        recommended = None
        for opt in options:
            s = self.score_option(opt, context)
            if s < best_score:
                best_score = s
                recommended = opt

        # Determine explicit rationale
        rationale = "This option balances cost and time."
        if recommended.mode == "ride_hailing":
             rationale = "Fastest convenience with minimum wait time."
        elif recommended.mode == "public_transit":
             rationale = "Lowest environmental impact and cheapest option. Ideal for preserving financial index."

        return {
             "origin": origin,
             "destination": destination,
             "distance_km": round(distance_km, 1),
             "options": [o.model_dump() for o in options],
             "recommended_option": recommended.model_dump() if recommended else None,
             "rationale": rationale,
             "actions": [
                 {"action": "book_ride", "mode": "ride_hailing", "is_available": True, "description": "Book Uber/Careem"}
             ]
        }
