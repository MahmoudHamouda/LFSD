"""
Uber API Service

Provides integration with Uber's API for ride price estimates and requests.
Operational implementation using real API and User Context.
"""

import httpx
from typing import Optional, Dict, Any, List
from core.config import get_settings
from models.models import Connection
from sqlalchemy.orm import Session
from loguru import logger
import json
from datetime import datetime

class UberService:
    """Service for interacting with Uber API."""
    
    BASE_URL = "https://api.uber.com/v1.2"
    
    def __init__(self, db: Session):
        self.settings = get_settings()
        self.db = db
        # Fallback for general estimates if no user context, though deprecated
        self.server_token = self.settings.UBER_SERVER_TOKEN 
        
    def _get_headers(self, access_token: Optional[str] = None) -> Dict[str, str]:
        """
        Get headers for Uber API requests.
        Prioritizes User Access Token, falls back to Server Token (for estimates only).
        """
        if access_token:
            return {
                "Authorization": f"Bearer {access_token}",
                "Accept-Language": "en_US",
                "Content-Type": "application/json"
            }
        elif self.server_token:
             return {
                "Authorization": f"Token {self.server_token}",
                "Accept-Language": "en_US",
                "Content-Type": "application/json"
            }
        else:
            raise ValueError("No valid Uber credentials available (Access Token or Server Token required)")

    def _get_user_token(self, user_id: str) -> Optional[str]:
        """Retrieve valid access token for user."""
        conn = self.db.query(Connection).filter(
            Connection.user_id == user_id,
            Connection.provider == "uber"
        ).first()
        
        if conn and conn.status == "connected":
            # TODO: Add Token Refresh Logic here if expired
            return conn.access_token
        return None
    
    async def get_price_estimates(
        self,
        start_latitude: float,
        start_longitude: float,
        end_latitude: Optional[float] = None,
        end_longitude: Optional[float] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get price estimates for rides from start to end location.
        """
        # Validate Inputs
        if start_latitude is None or start_longitude is None:
             return {"error": "Start location coordinates are required"}
        
        if not (-90 <= start_latitude <= 90) or not (-180 <= start_longitude <= 180):
             return {"error": "Invalid start coordinates"}

        token = None
        if user_id:
            token = self._get_user_token(user_id)
        
        try:
            headers = self._get_headers(access_token=token)
        except ValueError:
             return {"error": "Uber integration not configured (Missing Credentials)"}

        params = {
            "start_latitude": start_latitude,
            "start_longitude": start_longitude,
        }
        
        if end_latitude is not None and end_longitude is not None:
             if not (-90 <= end_latitude <= 90) or not (-180 <= end_longitude <= 180):
                 return {"error": "Invalid end coordinates"}
             params["end_latitude"] = end_latitude
             params["end_longitude"] = end_longitude
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/estimates/price",
                    params=params,
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "success": True,
                        "prices": data.get("prices", []),
                        "mock": False
                    }
                else:
                    logger.error(f"Uber API Error (Estimates): {response.status_code} - {response.text}")
                    return {
                        "error": f"Uber API unavailable: {response.text}",
                        "mock": False
                    }
                    
        except httpx.RequestError as e:
            logger.error(f"Uber Network Error: {e}")
            return {"error": "Failed to connect to Uber API"}
        except Exception as e:
            logger.exception("Unexpected error in Uber estimates")
            return {"error": str(e)}

    
    async def book_ride(
        self,
        user_id: str,
        product_id: str,
        start_location: Dict[str, Any],
        end_location: Dict[str, Any],
        fare_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Book a ride for the user. Requires valid User Access Token.
        """
        token = self._get_user_token(user_id)
        if not token:
            return {"error": "User is not connected to Uber. Please connect your account."}
            
        headers = self._get_headers(access_token=token)
        
        # Unpack locations
        try:
            payload = {
                "product_id": product_id,
                "start_latitude": start_location["latitude"],
                "start_longitude": start_location["longitude"],
                "end_latitude": end_location["latitude"],
                "end_longitude": end_location["longitude"]
            }
            if fare_id:
                payload["fare_id"] = fare_id
        except KeyError as e:
            return {"error": f"Missing location data: {e}"}

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.BASE_URL}/requests",
                    json=payload,
                    headers=headers,
                    timeout=15.0
                )
                
                if response.status_code in [200, 202]:
                    data = response.json()
                    return {
                        "success": True,
                        "ride_id": data.get("request_id"),
                        "status": data.get("status"),
                        "eta": data.get("eta"), # Minutes
                        "details": data
                    }
                elif response.status_code == 409:
                    error_data = response.json()
                    return {"error": f"Booking conflict: {error_data.get('message')}"} 
                else:
                    logger.error(f"Uber Booking Error: {response.status_code} - {response.text}")
                    return {"error": "Failed to book ride with Uber provider."}
                    
        except Exception as e:
            logger.exception("Error in book_ride")
            return {"error": str(e)}

    def format_price_response(self, api_response: Dict[str, Any]) -> str:
        """Format API response into a user-friendly message."""
        if api_response.get("error"):
            # Don't show technical errors to user unless necessary
            return f"Unable to fetch Uber prices at the moment. ({api_response['error']})"
        
        prices = api_response.get("prices", [])
        if not prices:
            return "No Uber options available in this area."
        
        lines = ["🚗 **Real-time Uber Estimates:**\n"]
        # Filter for reasonable products (e.g. not 'UberCOPTER' unless you want)
        for price in prices[:4]:
            name = price.get("localized_display_name", price.get("display_name", "Ride"))
            estimate = price.get("estimate", "N/A")
            duration = int(price.get("duration", 0) / 60)
            
            lines.append(f"- **{name}**: {estimate} (~{duration} min)")
        
        lines.append("\n*Prices and availability subject to change.*")
        return "\n".join(lines)
