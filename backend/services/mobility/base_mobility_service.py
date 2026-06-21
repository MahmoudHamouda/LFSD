"""
Base Mobility Service - Absolute interface for all mobility providers.

Defines the contract for mobility providers (Uber, Careem, Bolt, RTA).
This class is a pure interface; it contains no persistence or domain logic.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class PriceEstimate(BaseModel):
    """Standardized price estimate response."""

    provider: str
    ride_type: str
    display_name: str
    estimate: str
    low_estimate: float
    high_estimate: float
    duration: int  # Seconds
    distance: float  # Kilometers
    currency: str = "AED"
    mock: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MobilityBookingResponse(BaseModel):
    """Standardized booking response."""

    success: bool
    ride_id: Optional[str] = None
    status: str
    provider: str
    message: Optional[str] = None
    estimated_cost: Optional[float] = None
    currency: str = "AED"
    eta: Optional[int] = None  # Minutes
    driver_info: Optional[Dict[str, Any]] = None
    mock: bool = False
    error: Optional[str] = None


class BaseMobilityService(ABC):
    """
    Abstract interface for all mobility providers.
    Implementations must be stateless and database-agnostic.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider identifier (e.g., 'uber', 'rta')."""

        raise NotImplementedError

    @abstractmethod
    async def get_price_estimates(
        self,
        start_lat: float,
        start_lng: float,
        end_lat: Optional[float] = None,
        end_lng: Optional[float] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get price estimates for rides.

        Returns:
            Dict matching the PriceEstimate schema.
        """

        raise NotImplementedError

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

        Returns:
            Dict matching the MobilityBookingResponse schema.
        """

        raise NotImplementedError

    @abstractmethod
    async def get_ride_status(self, user_id: str, ride_id: str) -> Dict[str, Any]:
        """
        Get status of an active ride.
        """

        raise NotImplementedError
