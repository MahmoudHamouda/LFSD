"""
Google Maps Service

Handles location-related operations using the Google Maps Platform API.
Includes geocoding, reverse geocoding, and distance matrix calculations.
"""

import httpx
import logging
import asyncio
import googlemaps
import core.config
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import urllib.parse

logger = logging.getLogger(__name__)


class GoogleMapsService:
    """
    Service for interacting with Google Maps Platform APIs.
    Uses a persistent client for connection pooling and implements retries.
    """

    BASE_URL = "https://maps.googleapis.com/maps/api"
    _client: Optional[httpx.AsyncClient] = None

    def __init__(self):
        self.settings = core.config.get_settings()
        self.api_key = self.settings.GOOGLE_MAPS_API_KEY
        self.client = None
        if self.settings.GOOGLE_MAPS_API_KEY:
            # Default region/language for better relevance
            self.region = "ae"
            self.language = "en"

    @classmethod
    async def get_client(cls) -> httpx.AsyncClient:
        """Get or create the persistent AsyncClient for connection pooling."""
        if cls._client is None or cls._client.is_closed:
            cls._client = httpx.AsyncClient(
                timeout=httpx.Timeout(10.0, connect=5.0),
                limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            )
        return cls._client

    async def geocode(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Convert an address to latitude and longitude.

        Args:
            address: The address to geocode (e.g., "Dubai Mall")

        Returns:
            Tuple of (lat, lng), or None if not found or error.
        """
        if not address:
            return None

        if not self.api_key or self.api_key == "mock":
            logger.info("Using mock geocoding for address.")
            return self._get_mock_coordinates(address)

        params = {
            "address": address,
            "key": self.api_key,
            "region": self.region,
            "language": self.language,
        }

        try:
            client = await self.get_client()
            # Implement 1 retry for transient network issues
            for attempt in range(2):
                try:
                    response = await client.get(
                        f"{self.BASE_URL}/geocode/json", params=params
                    )
                    response.raise_for_status()
                    data = response.json()

                    status = data.get("status")
                    if status == "OK" and data.get("results"):
                        location = data["results"][0]["geometry"]["location"]
                        return location["lat"], location["lng"]
                    elif status == "ZERO_RESULTS":
                        logger.info(
                            f"Geocoding found no results for: [REDACTED ADDRESS]"
                        )
                        return None
                    elif status in ["OVER_QUERY_LIMIT", "REQUEST_DENIED"]:
                        logger.error(
                            f"Google Maps API error: {status}. Message: {data.get('error_message')}"
                        )
                        break  # Unrecoverable here
                    else:
                        logger.warning(f"Geocoding failed for [REDACTED]: {status}")
                        break
                except (httpx.RequestError, httpx.TimeoutException) as e:
                    if attempt == 0:
                        await asyncio.sleep(1)
                        continue
                    logger.error(f"Geocoding network error: {e}")

        except Exception as e:
            logger.error(f"Geocoding exception: {type(e).__name__}")

        return None

    async def reverse_geocode(self, lat: float, lng: float) -> Optional[str]:
        """
        Convert latitude and longitude to a human-readable address.
        """
        if not self.api_key or self.api_key == "mock":
            # Better mock: return at least based on coords
            if 25.0 <= lat <= 26.0 and 55.0 <= lng <= 56.0:
                return "Mock Address, Downtown Dubai, UAE"
            return "Mock Address, Unknown Location"

        params = {
            "latlng": f"{lat},{lng}",
            "key": self.api_key,
            "language": self.language,
        }

        try:
            client = await self.get_client()
            response = await client.get(f"{self.BASE_URL}/geocode/json", params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "OK" and data.get("results"):
                return data["results"][0]["formatted_address"]
        except Exception as e:
            logger.error(f"Reverse geocoding exception: {type(e).__name__}")

        return None

    async def get_distance_matrix(
        self, origins: List[str], destinations: List[str], mode: str = "driving"
    ) -> Optional[Dict[str, Any]]:
        """
        Get travel distance and time between origins and destinations.
        """
        if not origins or not destinations:
            return None

        # Validation
        if len(origins) > 25 or len(destinations) > 25:
            logger.error("Distance matrix exceeded 25 origins/destinations limit.")
            return None

        valid_modes = ["driving", "walking", "bicycling", "transit"]
        if mode not in valid_modes:
            mode = "driving"

        if not self.api_key or self.api_key == "mock":
            return self._get_mock_distance_matrix(len(origins), len(destinations))

        params = {
            "origins": "|".join(origins),
            "destinations": "|".join(destinations),
            "mode": mode,
            "key": self.api_key,
            "units": "metric",
        }

        try:
            client = await self.get_client()
            response = await client.get(
                f"{self.BASE_URL}/distancematrix/json", params=params
            )
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "OK":
                return data
            else:
                logger.error(f"Distance matrix API error: {data.get('status')}")
        except Exception as e:
            logger.error(f"Distance matrix exception: {type(e).__name__}")

        return None

    def _get_mock_coordinates(self, address: str) -> Tuple[float, float]:
        """Return mock coordinates for common locations, avoiding Dubai default for everything."""
        addr = address.lower()
        if "dubai" in addr or "dxb" in addr:
            if "mall" in addr:
                return 25.1972, 55.2744
            if "airport" in addr:
                return 25.2532, 55.3657
            return 25.2048, 55.2708
        elif "cairo" in addr or "egypt" in addr:
            if "pyramid" in addr:
                return 29.9792, 31.1342
            if "airport" in addr:
                return 30.1219, 31.4056
            return 30.0444, 31.2357
        elif "london" in addr:
            return 51.5074, -0.1278

        # Truly unknown
        return 0.0, 0.0

    def _get_mock_distance_matrix(
        self, num_origins: int, num_destinations: int
    ) -> Dict[str, Any]:
        """Return more realistic mock distance matrix data."""
        rows = []
        for _ in range(num_origins):
            elements = []
            for _ in range(num_destinations):
                elements.append(
                    {
                        "status": "OK",
                        "duration": {"text": "22 mins", "value": 1320},
                        "distance": {"text": "12.5 km", "value": 12500},
                    }
                )
            rows.append({"elements": elements})

        return {
            "status": "OK",
            "rows": rows,
            "origin_addresses": ["Mock Origin (MOCK_MODE)"] * num_origins,
            "destination_addresses": ["Mock Destination (MOCK_MODE)"]
            * num_destinations,
        }


def get_google_maps_service() -> GoogleMapsService:
    """Factory function to provide the service."""
    return GoogleMapsService()
