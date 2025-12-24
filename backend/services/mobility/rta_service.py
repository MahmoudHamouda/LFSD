"""
RTA (Roads and Transport Authority) API Service

Provides integration with RTA's API for public transit routes and schedules.
"""

import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime
from core.config import get_settings
from .base_mobility_service import BaseMobilityService


class RTAService(BaseMobilityService):
    """Service for interacting with RTA API (Public Transit)."""
    
    # Hypothetical Base URL
    BASE_URL = "https://api.rta.ae/v1"
    
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.RTA_API_KEY
    
    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "rta"
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for RTA API requests."""
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
        Get price estimates (trip cost) for public transit.
        """
        if not self.api_key:
            return {
                "error": "RTA API key not configured",
                "mock": True,
                "prices": self._get_mock_prices()
            }
        
        try:
            # Hypothetical API call
            # Simulating API call failure to use mock data for now
            raise Exception("RTA API not reachable (Mock Mode)")
                    
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
        Book a ride (or buy a ticket) with RTA.
        """
        # For public transit, "booking" usually means buying a ticket or generating a QR code
        ticket_id = f"rta_{user_id}_{int(datetime.now().timestamp())}"
        
        # Log the booking attempt
        self.log_booking(
            user_id,
            ticket_id,
            ride_type,
            {
                "start": start_location,
                "end": end_location,
                "mock": True
            },
            status="confirmed" # Tickets are usually instant
        )
        
        self.log_interaction(
            user_id,
            "booking",
            {
                "ticket_id": ticket_id,
                "ride_type": ride_type,
                "start": start_location,
                "end": end_location,
                "mock": True
            }
        )
        
        return {
            "success": True,
            "ride_id": ticket_id,
            "status": "confirmed",
            "mock": True,
            "message": "RTA Ticket Generated (Mock Response)",
            "details": {
                "ticket_type": "Single Trip",
                "zones": "Zone 1 -> Zone 2",
                "valid_until": "2 hours from now"
            },
            "eta": 0 # Immediate
        }
    
    def _get_mock_prices(self) -> List[Dict[str, Any]]:
        """Return mock RTA price data (Metro/Bus)."""
        return [
            {
                "localized_display_name": "Dubai Metro (Red Line)",
                "estimate": "AED 5.00",
                "low_estimate": 5.0,
                "high_estimate": 5.0,
                "duration": 1200, # 20 mins
                "distance": 15.0,
                "currency": "AED",
                "type": "public_transit"
            },
            {
                "localized_display_name": "RTA Bus (Route 8)",
                "estimate": "AED 3.00",
                "low_estimate": 3.0,
                "high_estimate": 3.0,
                "duration": 2400, # 40 mins
                "distance": 15.0,
                "currency": "AED",
                "type": "public_transit"
            }
        ]
