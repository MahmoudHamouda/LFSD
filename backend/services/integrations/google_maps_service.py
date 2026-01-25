"""
Google Maps Service - Hardened for Production.

Provides geocoding and distance matrix calculations using the official Google Maps Python SDK.
Standardized with structured logging, robust error handling, and connection validation.
"""

import logging
import googlemaps
from datetime import datetime
import core.config
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class GoogleMapsService:
    """
    Service for geocoding and routing analytics.
    Ensures graceful degradation if API keys are missing.
    """
    def __init__(self):
        self.settings = core.config.get_settings()
        self.api_key = self.settings.GOOGLE_MAPS_API_KEY
        self.client = None
        
        if self.api_key:
            try:
                # The googlemaps client handles its own connection pooling
                self.client = googlemaps.Client(key=self.api_key, timeout=10)
            except Exception as e:
                logger.error(f"Failed to initialize Google Maps client: {e}")
        else:
            logger.warning("Google Maps API key is missing. Maps features will be disabled.")

    def geocode(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Geocode an address string to safe (latitude, longitude) coordinates.
        """
        if not self.client:
            logger.error("Attempted geocode without initialized Google Maps client.")
            return None
            
        if not address or not address.strip():
            logger.warning("Received empty address for geocoding.")
            return None

        try:
            # Result is a list of address components
            result = self.client.geocode(address)
            if result and len(result) > 0:
                location = result[0].get('geometry', {}).get('location', {})
                lat = location.get('lat')
                lng = location.get('lng')
                
                if lat is not None and lng is not None:
                    logger.debug(f"Geocoded '{address}' to ({lat}, {lng})")
                    return float(lat), float(lng)
            
            logger.info(f"No geocoding results found for address: {address}")
            return None
            
        except Exception as e:
            logger.error(f"Google Maps Geocoding Error for '{address}': {e}")
            return None

    def get_distance(self, origin: str, destination: str) -> Optional[float]:
        """
        Calculate driving distance in kilometers between two points.
        Returns None if calculation fails or locations are unreachable.
        """
        if not self.client:
            return None
            
        if not origin or not destination:
            return None

        try:
            result = self.client.distance_matrix(
                origins=[origin],
                destinations=[destination],
                mode="driving",
                units="metric"
            )
            
            # Navigate nested Google response structure
            rows = result.get('rows', [])
            if not rows:
                return None
                
            elements = rows[0].get('elements', [])
            if not elements:
                return None
                
            element = elements[0]
            if element.get('status') == 'OK':
                # 'value' is returned in meters by Google
                meters = element.get('distance', {}).get('value', 0)
                logger.debug(f"Distance from {origin} to {destination}: {meters}m")
                return meters / 1000.0
            else:
                logger.info(f"Distance calculation failed: {element.get('status')} for {origin} -> {destination}")
                return None
                
        except Exception as e:
            logger.error(f"Google Maps Distance Matrix Error: {e}")
            return None
