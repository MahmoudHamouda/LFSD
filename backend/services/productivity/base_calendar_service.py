"""
Base Calendar Service

Abstract base class and normalized schemas for calendar providers.
Ensures consistency across Google, Outlook, and other integrations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timezone
from dataclasses import dataclass, field
import enum
import logging

logger = logging.getLogger(__name__)

class EventStatus(enum.Enum):
    CONFIRMED = "confirmed"
    TENTATIVE = "tentative"
    CANCELLED = "cancelled"

class BusyStatus(enum.Enum):
    FREE = "free"
    BUSY = "busy"
    TENTATIVE = "tentative"
    OOF = "oof" # Out of Office / Working Elsewhere

@dataclass
class NormalizedEvent:
    """Standardized representation of a calendar event."""
    id: str
    summary: str
    start_time: datetime # Must be timezone-aware
    end_time: datetime   # Must be timezone-aware
    
    description: Optional[str] = None
    location: Optional[str] = None
    status: EventStatus = EventStatus.CONFIRMED
    busy_status: BusyStatus = BusyStatus.BUSY
    is_all_day: bool = False
    
    # Provider-specific metadata
    provider_id: Optional[str] = None
    account_id: Optional[str] = None
    calendar_id: Optional[str] = None
    
    # Original raw data object
    raw: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        # Enforce timezone awareness
        if self.start_time.tzinfo is None:
            self.start_time = self.start_time.replace(tzinfo=timezone.utc)
        if self.end_time.tzinfo is None:
            self.end_time = self.end_time.replace(tzinfo=timezone.utc)

@dataclass
class CalendarAccount:
    """Represents a specific calendar account (e.g. Work vs Personal)."""
    id: str
    provider: str # 'google', 'outlook'
    email: str
    is_primary: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

class CalendarServiceError(Exception):
    """Base exception for calendar service errors."""
    pass

class CalendarAuthError(CalendarServiceError):
    """Raised when authentication fails or token is expired."""
    pass

class CalendarRateLimitError(CalendarServiceError):
    """Raised when provider rate limits are hit."""
    pass

class BaseCalendarService(ABC):
    """
    Abstract base class for calendar services.
    Implementations must return NormalizedEvent objects and handle UTC awareness.
    """
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the system key for this provider (e.g., 'google_calendar')."""
        raise NotImplementedError
        
    @abstractmethod
    async def list_calendars(self, user_id: str, account_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available calendars for the user's account."""
        raise NotImplementedError

    @abstractmethod
    async def list_events(
        self, 
        user_id: str, 
        time_min: datetime, 
        time_max: datetime,
        account_id: Optional[str] = None,
        calendar_id: str = "primary",
        limit: int = 250
    ) -> List[NormalizedEvent]:
        """
        List events within a time range.
        Should return events that OVERLAP the [time_min, time_max] interval.
        """
        """
        raise NotImplementedError
        
    @abstractmethod
    async def create_event(
        self,
        user_id: str,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
        account_id: Optional[str] = None,
        calendar_id: str = "primary",
        idempotency_key: Optional[str] = None
    ) -> NormalizedEvent:
        """Create a new calendar event with built-in idempotency support."""
        """Create a new calendar event with built-in idempotency support."""
        raise NotImplementedError

    @abstractmethod
    async def delete_event(
        self,
        user_id: str,
        event_id: str,
        account_id: Optional[str] = None,
        calendar_id: str = "primary"
    ) -> bool:
        """Delete an event by ID."""
        """Delete an event by ID."""
        raise NotImplementedError
        
    @abstractmethod
    async def check_availability(
        self,
        user_id: str,
        start_time: datetime,
        end_time: datetime,
        account_id: Optional[str] = None,
        calendar_id: str = "primary"
    ) -> BusyStatus:
        """
        Check availability for a specific slot.
        Returns the highest level of 'busyness' detected.
        """
        """
        raise NotImplementedError

    def _ensure_utc(self, dt: datetime) -> datetime:
        """Helper to ensure awareness."""
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
