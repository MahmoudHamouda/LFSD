"""
Uber API Service

Provides integration with Uber's API for ride price estimates and requests.
Uses the Uber Server Token for authentication.
Supports both Sandbox (dev) and Production modes.
"""

import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime
import core.config
from services.connection_service import ConnectionService
from .base_mobility_service import BaseMobilityService
from sqlalchemy.orm import Session
import logging
import uuid

logger = logging.getLogger(__name__)


class UberService(BaseMobilityService):
    """Service for interacting with Uber API (Sandbox or Production)."""
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.settings = core.config.get_settings()
        if db:
            self.connection_service = ConnectionService(db)
        self.server_token = self.settings.UBER_SERVER_TOKEN
        
        # Use Sandbox in development, Production in prod
        if self.settings.ENV == "dev":
            self.base_url = "https://sandbox-api.uber.com/v1.2"
        else:
            self.base_url = "https://api.uber.com/v1.2"
    
    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "uber"
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Uber API requests."""
        return {
            "Authorization": f"Token {self.server_token}",
            "Accept-Language": "en_US",
            "Content-Type": "application/json"
        }
    
    async def get_price_estimates(
        self,
        start_lat: float,
        start_lng: float,
        end_lat: Optional[float] = None,
        end_lng: Optional[float] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get price estimates for rides from start to end location.
        
        Args:
            start_lat: Starting latitude
            start_lng: Starting longitude
            end_lat: Ending latitude (optional)
            end_lng: Ending longitude (optional)
            user_id: User ID for logging (optional)
            
        Returns:
            Dictionary with price estimates or error information
        """
        # Calculate approximate distance for mock pricing
        distance_km = 10.0
        if start_lat and start_lng and end_lat and end_lng:
            from math import radians, cos, sin, asin, sqrt
            # Haversine formula
            lon1, lat1, lon2, lat2 = map(radians, [start_lng, start_lat, end_lng, end_lat])
            dlon = lon2 - lon1 
            dlat = lat2 - lat1 
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a)) 
            r = 6371 # Radius of earth in kilometers
            distance_km = c * r
            
        if not self.server_token:
            return {
                "error": "Uber API token not configured",
                "mock": True,
                "prices": self._get_mock_prices(distance_km)
            }
        
        try:
            params = {
                "start_latitude": start_lat,
                "start_longitude": start_lng,
            }
            
            if end_lat and end_lng:
                params["end_latitude"] = end_lat
                params["end_longitude"] = end_lng
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/estimates/price",
                    params=params,
                    headers=self._get_headers(),
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    prices = data.get("prices", [])
                    
                    return {
                        "success": True,
                        "prices": prices,
                        "mock": False,
                        "sandbox": self.settings.ENV == "dev"
                    }
                else:
                    logger.error(f"Uber API error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"API returned {response.status_code}",
                        "mock": True,
                        "prices": self._get_mock_prices(distance_km)
                    }
                    
        except Exception as e:
            logger.error(f"Uber API exception: {e}")
            return {
                "success": False,
                "error": str(e),
                "mock": True,
                "prices": self._get_mock_prices(distance_km)
            }
    
    async def book_ride(
        self,
        user_id: str,
        ride_type: str,
        start_location: Dict[str, Any],
        end_location: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Book a ride (Mock/Sandbox)."""
        ride_id = f"uber_{uuid.uuid4().hex[:12]}"
        
        return {
            "success": True,
            "ride_id": ride_id,
            "status": "pending",
            "provider": self.provider_name,
            "mock": True,
            "message": "Uber booking initiated in sandbox mode.",
            "driver_info": {
                "name": "Ahmed",
                "rating": 4.9,
                "vehicle": "Toyota Camry",
                "plate": "Dubai 12345"
            },
            "eta": 5
        }

    async def get_ride_status(self, user_id: str, ride_id: str) -> Dict[str, Any]:
        """Fetch tracking status for an active Uber ride."""
        return {
            "success": True,
            "status": "in_progress",
            "ride_id": ride_id,
            "provider": self.provider_name,
            "eta": 12,
            "mock": True
        }

    async def get_active_bookings(self, user_id: str) -> List[Dict[str, Any]]:
        """Get active bookings for the user."""
        if not hasattr(self, 'active_bookings'):
            self.active_bookings = []
        return self.active_bookings
    
    def _get_mock_prices(self, distance_km: float = 10.0) -> List[Dict[str, Any]]:
        """Return mock Uber price data as fallback, scaled by distance."""
        # Base rates (approximate)
        rates = {
            "UberX": {"base": 12, "per_km": 2.5},
            "UberXL": {"base": 18, "per_km": 3.5},
            "Uber Black": {"base": 25, "per_km": 5.0}
        }
        
        prices = []
        for name, rate in rates.items():
            cost = rate["base"] + (rate["per_km"] * distance_km)
            low = round(cost * 0.9)
            high = round(cost * 1.1)
            
            prices.append({
                "localized_display_name": name,
                "estimate": f"AED {low}-{high}",
                "low_estimate": low,
                "high_estimate": high,
                "duration": int(distance_km * 60), # Approx 1 min per km
                "distance": distance_km,
                "currency": "AED"
            })
            
        return prices
