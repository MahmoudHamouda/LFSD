"""
Google Maps Service

Handles location-related operations using the Google Maps Platform API.
Includes geocoding, reverse geocoding, and distance matrix calculations.
"""

import httpx
from typing import Optional, Dict, Any, List, Tuple
from core.config import get_settings
import logging

logger = logging.getLogger(__name__)

class GoogleMapsService:
    """Service for interacting with Google Maps Platform APIs."""
    
    BASE_URL = "https://maps.googleapis.com/maps/api"
    
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.GOOGLE_MAPS_API_KEY
        
    async def geocode(self, address: str) -> Optional[Dict[str, float]]:
        """
        Convert an address to latitude and longitude.
        
        Args:
            address: The address to geocode (e.g., "Dubai Mall")
            
        Returns:
            Dict with 'lat' and 'lng' keys, or None if not found.
        """
        if not self.api_key:
            logger.warning("Google Maps API key not configured. Returning mock coordinates.")
            return self._get_mock_coordinates(address)
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/geocode/json",
                    params={
                        "address": address,
                        "key": self.api_key
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "OK" and data.get("results"):
                        location = data["results"][0]["geometry"]["location"]
                        return {"lat": location["lat"], "lng": location["lng"]}
                    else:
                        logger.warning(f"Geocoding failed for '{address}': {data.get('status')}")
                else:
                    logger.error(f"Google Maps API error: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Geocoding exception: {e}")
            
        return None

    async def reverse_geocode(self, lat: float, lng: float) -> Optional[str]:
        """
        Convert latitude and longitude to a human-readable address.
        
        Args:
            lat: Latitude
            lng: Longitude
            
        Returns:
            Formatted address string, or None if not found.
        """
        if not self.api_key:
            return "Mock Address, Dubai, UAE"
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/geocode/json",
                    params={
                        "latlng": f"{lat},{lng}",
                        "key": self.api_key
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "OK" and data.get("results"):
                        return data["results"][0]["formatted_address"]
        except Exception as e:
            logger.error(f"Reverse geocoding exception: {e}")
            
        return None

    async def get_distance_matrix(
        self, 
        origins: List[str], 
        destinations: List[str],
        mode: str = "driving"
    ) -> Optional[Dict[str, Any]]:
        """
        Get travel distance and time between origins and destinations.
        
        Args:
            origins: List of starting points (addresses or "lat,lng")
            destinations: List of destinations
            mode: Travel mode (driving, walking, bicycling, transit)
            
        Returns:
            Distance matrix response or None.
        """
        if not self.api_key:
            return self._get_mock_distance_matrix(len(origins), len(destinations))
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/distancematrix/json",
                    params={
                        "origins": "|".join(origins),
                        "destinations": "|".join(destinations),
                        "mode": mode,
                        "key": self.api_key
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "OK":
                        return data
        except Exception as e:
            logger.error(f"Distance matrix exception: {e}")
            
        return None

    def _get_mock_coordinates(self, address: str) -> Dict[str, float]:
        """Return mock coordinates for common Dubai locations."""
        address_lower = address.lower()
        if "dubai mall" in address_lower:
            return {"lat": 25.1972, "lng": 55.2744}
        elif "marina" in address_lower:
            return {"lat": 25.0805, "lng": 55.1403}
        elif "airport" in address_lower or "dxb" in address_lower:
            return {"lat": 25.2532, "lng": 55.3657}
        elif "jbr" in address_lower:
            return {"lat": 25.0776, "lng": 55.1305}
        elif "palm" in address_lower:
            return {"lat": 25.1124, "lng": 55.1390}
        else:
            # Default to Downtown Dubai
            return {"lat": 25.2048, "lng": 55.2708}

    def _get_mock_distance_matrix(self, num_origins: int, num_destinations: int) -> Dict[str, Any]:
        """Return mock distance matrix data."""
        rows = []
        for _ in range(num_origins):
            elements = []
            for _ in range(num_destinations):
                elements.append({
                    "status": "OK",
                    "duration": {"text": "15 mins", "value": 900},
                    "distance": {"text": "10 km", "value": 10000}
                })
            rows.append({"elements": elements})
            
        return {
            "status": "OK",
            "rows": rows,
            "origin_addresses": ["Mock Origin"] * num_origins,
            "destination_addresses": ["Mock Destination"] * num_destinations
        }

# Singleton instance
_google_maps_service = None

def get_google_maps_service() -> GoogleMapsService:
    """Get or create the Google Maps service singleton."""
    global _google_maps_service
    if _google_maps_service is None:
        _google_maps_service = GoogleMapsService()
    return _google_maps_service
