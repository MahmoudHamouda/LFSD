
import googlemaps
from core.config import get_settings
from typing import Dict, Optional, Tuple

class GoogleMapsService:
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.GOOGLE_MAPS_API_KEY
        self.client = None
        if self.api_key:
            try:
                self.client = googlemaps.Client(key=self.api_key)
            except Exception as e:
                print(f"Error initializing Google Maps client: {e}")

    def geocode(self, address: str) -> Optional[Tuple[float, float]]:
        """
        Geocode an address string to (lat, lng).
        """
        if not self.client:
            print("Google Maps client not initialized.")
            return None
            
        try:
            result = self.client.geocode(address)
            if result:
                location = result[0]['geometry']['location']
                return location['lat'], location['lng']
        except Exception as e:
            print(f"Geocoding error: {e}")
            return None
        return None

    def get_distance(self, origin: str, destination: str) -> Optional[float]:
        """
        Get driving distance in km between two locations.
        """
        if not self.client:
            return None
            
        try:
            result = self.client.distance_matrix(
                origins=[origin],
                destinations=[destination],
                mode="driving",
                units="metric"
            )
            
            if result['rows'][0]['elements'][0]['status'] == 'OK':
                distance_text = result['rows'][0]['elements'][0]['distance']['text']
                distance_value = result['rows'][0]['elements'][0]['distance']['value'] # meters
                return distance_value / 1000.0 # km
        except Exception as e:
            print(f"Distance matrix error: {e}")
            return None
        return None
