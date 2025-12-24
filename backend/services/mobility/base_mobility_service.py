"""
Base Mobility Service - Abstract interface for all mobility providers.

This module defines the abstract base class that all mobility providers
(Uber, Careem, Bolt, RTA) must implement to ensure consistency.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime
from models.database import SessionLocal
from models.models import VivLog, MobilityTrip
import uuid
import json


class BaseMobilityService(ABC):
    """Abstract base class for all mobility providers."""
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Return the provider name (e.g., 'uber', 'careem', 'bolt', 'rta').
        
        Returns:
            str: Provider identifier
        """
        pass
    
    @abstractmethod
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
            Dictionary with structure:
            {
                "success": bool,
                "prices": List[Dict],
                "mock": bool,
                "error": str (optional)
            }
        """
        pass
    
    @abstractmethod
    async def book_ride(
        self,
        user_id: str,
        ride_type: str,
        start_location: Dict[str, Any],
        end_location: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Book a ride with this provider.
        
        Args:
            user_id: User ID
            ride_type: Type of ride (e.g., "UberX", "Careem GO")
            start_location: Dict with lat, lng, address
            end_location: Dict with lat, lng, address
            **kwargs: Provider-specific options
            
        Returns:
            Dictionary with booking details:
            {
                "success": bool,
                "ride_id": str,
                "status": str,
                "driver": Dict (optional),
                "eta": int (optional),
                "error": str (optional)
            }
        """
        pass
    
    async def get_ride_status(
        self,
        user_id: str,
        ride_id: str
    ) -> Dict[str, Any]:
        """
        Get status of an active ride.
        
        Args:
            user_id: User ID
            ride_id: Ride identifier
            
        Returns:
            Dictionary with ride status:
            {
                "success": bool,
                "status": str,
                "driver": Dict (optional),
                "location": Dict (optional),
                "eta": int (optional),
                "error": str (optional)
            }
        """
        # Default implementation - providers can override
        return {
            "success": False,
            "error": "Ride tracking not implemented for this provider"
        }
    
    # Common helper methods (implemented in base class)
    
    def log_interaction(
        self,
        user_id: str,
        interaction_type: str,
        details: Dict[str, Any],
        conversation_id: Optional[str] = None
    ) -> None:
        """
        Log user interaction to database using VivLog.
        """
        try:
            db = SessionLocal()
            log = VivLog(
                id=str(uuid.uuid4()),
                user_id=user_id,
                user_intent=interaction_type,
                context_snapshot_json=details,
                decision_logic=f"{self.provider_name} Interaction",
                ai_response="Interaction recorded",
                timestamp=datetime.utcnow()
            )
            db.add(log)
            db.commit()
            db.close()
        except Exception as e:
            print(f"Failed to log interaction for {self.provider_name}: {e}")
    
    def log_price_history(
        self,
        user_id: str,
        prices: List[Dict[str, Any]],
        start_location: Dict[str, float],
        end_location: Optional[Dict[str, float]] = None
    ) -> None:
        """
        Log price estimates to history.
        (Disabled/Skipped as DBPriceHistory is removed)
        """
        pass
    
    def log_booking(
        self,
        user_id: str,
        ride_id: str,
        ride_type: str,
        details: Dict[str, Any],
        status: str = "pending"
    ) -> None:
        """
        Log a ride booking to database using MobilityTrip.
        """
        try:
            db = SessionLocal()
            # Extract details if possible
            cost = details.get("cost_amount") or details.get("estimate")
            if isinstance(cost, str):
                # Simple parsing if string
                try:
                    cost = float(cost.replace('$','').split('-')[0])
                except:
                    cost = 0.0

            trip = MobilityTrip(
                id=str(uuid.uuid4()),
                user_id=user_id,
                provider=self.provider_name,
                trip_type=ride_type,
                cost_amount=cost if isinstance(cost, (int, float)) else 0.0,
                currency="USD", # Default
                # We might not have lat/lon easily here without parsing details, 
                # but we can save what we have.
                # For now, just basic logging.
            )
            db.add(trip)
            db.commit()
            db.close()
        except Exception as e:
            print(f"Failed to log booking for {self.provider_name}: {e}")
