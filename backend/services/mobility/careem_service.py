"""
Careem API Service

Provides integration with Careem's API for ride price estimates and booking.
"""

import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime
import core.config
from sqlalchemy.orm import Session
from .base_mobility_service import BaseMobilityService
from services.connection_service import ConnectionService


class CareemService(BaseMobilityService):
    """Service for interacting with Careem API."""
    
    # Hypothetical Base URL - would be replaced with actual production URL
    BASE_URL = "https://api.careem.com/v2"
    
    def __init__(self, db: Session):
        self.db = db
        self.settings = core.config.get_settings()
        self.connection_service = ConnectionService(db)
        self.api_key = self.settings.CAREEM_API_KEY
        self.api_secret = self.settings.CAREEM_API_SECRET
    
    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "careem"
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Careem API requests."""
        return {
            "X-API-KEY": self.api_key,
            "X-API-SECRET": self.api_secret,
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
                "error": "Careem API key not configured",
                "mock": True,
                "prices": self._get_mock_prices()
            }
        
        try:
            # Hypothetical API call
            params = {
                "pickup_lat": start_lat,
                "pickup_lng": start_lng,
            }
            
            if end_lat and end_lng:
                params["dropoff_lat"] = end_lat
                params["dropoff_lng"] = end_lng
            
            async with httpx.AsyncClient() as client:
                # This is a placeholder URL and logic
                # In a real implementation, we would call the actual API
                # For now, we'll simulate a failure to trigger mock data
                # or if we had a real sandbox, we'd use that.
                
                # Simulating API call failure to use mock data for now
                raise Exception("Careem API not reachable (Mock Mode)")
                
                # Real implementation would be:
                # response = await client.get(
                #     f"{self.BASE_URL}/estimates",
                #     params=params,
                #     headers=self._get_headers(),
                #     timeout=10.0
                # )
                
                # if response.status_code == 200:
                #     ... process response ...
                # else:
                #     ... handle error ...
                    
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
        Book a ride with Careem.
        """
        ride_id = f"careem_{user_id}_{int(datetime.now().timestamp())}"
        
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
            "message": "Careem booking (Mock Response)",
            "driver": {
                "name": "Muhammad",
                "rating": 4.8,
                "vehicle": "Lexus ES",
                "plate": "Dubai 54321"
            },
            "eta": 7
        }
    
    def _get_mock_prices(self) -> List[Dict[str, Any]]:
        """Return mock Careem price data."""
        return [
            {
                "localized_display_name": "Careem GO",
                "estimate": "AED 32-38",
                "low_estimate": 32,
                "high_estimate": 38,
                "duration": 300,
                "distance": 3.5,
                "currency": "AED"
            },
            {
                "localized_display_name": "Careem Comfort",
                "estimate": "AED 42-48",
                "low_estimate": 42,
                "high_estimate": 48,
                "duration": 300,
                "distance": 3.5,
                "currency": "AED"
            },
            {
                "localized_display_name": "Careem Max",
                "estimate": "AED 65-75",
                "low_estimate": 65,
                "high_estimate": 75,
                "duration": 300,
                "distance": 3.5,
                "currency": "AED"
            }
        ]
