"""
Bolt API Service

Provides integration with Bolt's API for ride price estimates and booking.
"""

import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime
from core.config import get_settings
from .base_mobility_service import BaseMobilityService


class BoltService(BaseMobilityService):
    """Service for interacting with Bolt API."""
    
    # Hypothetical Base URL
    BASE_URL = "https://api.bolt.eu/v1"
    
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.BOLT_API_KEY
    
    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "bolt"
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Bolt API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
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
        """
        if not self.api_key:
            return {
                "error": "Bolt API key not configured",
                "mock": True,
                "prices": self._get_mock_prices()
            }
        
        try:
            # Hypothetical API call
            # Simulating API call failure to use mock data for now
            raise Exception("Bolt API not reachable (Mock Mode)")
                    
        except Exception as e:
            # Fallback to mock data
            prices = self._get_mock_prices()
            
            # Log interaction if user_id provided
            if user_id:
                self.log_interaction(
                    user_id,
                    "price_check",
                    {
                        "start": {"lat": start_lat, "lng": start_lng},
                        "end": {"lat": end_lat, "lng": end_lng} if end_lat else None,
                        "num_options": len(prices),
                        "mock": True
                    }
                )
                
                self.log_price_history(
                    user_id,
                    prices,
                    {"lat": start_lat, "lng": start_lng},
                    {"lat": end_lat, "lng": end_lng} if end_lat else None
                )

            return {
                "success": True,
                "prices": prices,
                "mock": True,
                "message": "Using mock data (API not configured)"
            }
    
    async def book_ride(
        self,
        user_id: str,
        ride_type: str,
        start_location: Dict[str, Any],
        end_location: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Book a ride with Bolt.
        """
        ride_id = f"bolt_{user_id}_{int(datetime.now().timestamp())}"
        
        # Log the booking attempt
        self.log_booking(
            user_id,
            ride_id,
            ride_type,
            {
                "start": start_location,
                "end": end_location,
                "mock": True
            },
            status="pending"
        )
        
        self.log_interaction(
            user_id,
            "booking",
            {
                "ride_id": ride_id,
                "ride_type": ride_type,
                "start": start_location,
                "end": end_location,
                "mock": True
            }
        )
        
        return {
            "success": True,
            "ride_id": ride_id,
            "status": "pending",
            "mock": True,
            "message": "Bolt booking (Mock Response)",
            "driver": {
                "name": "Dmitri",
                "rating": 4.7,
                "vehicle": "Kia Optima",
                "plate": "Dubai 98765"
            },
            "eta": 4
        }
    
    def _get_mock_prices(self) -> List[Dict[str, Any]]:
        """Return mock Bolt price data."""
        return [
            {
                "localized_display_name": "Bolt",
                "estimate": "AED 30-36",
                "low_estimate": 30,
                "high_estimate": 36,
                "duration": 240,
                "distance": 3.5,
                "currency": "AED"
            },
            {
                "localized_display_name": "Bolt Premium",
                "estimate": "AED 45-55",
                "low_estimate": 45,
                "high_estimate": 55,
                "duration": 240,
                "distance": 3.5,
                "currency": "AED"
            },
            {
                "localized_display_name": "Bolt XL",
                "estimate": "AED 55-65",
                "low_estimate": 55,
                "high_estimate": 65,
                "duration": 300,
                "distance": 3.5,
                "currency": "AED"
            }
        ]
