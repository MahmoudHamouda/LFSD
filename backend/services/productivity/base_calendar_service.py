"""
Base Calendar Service

Abstract base class for calendar providers (Google, Outlook, Apple).
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class BaseCalendarService(ABC):
    """Abstract base class for calendar services."""
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of the provider (e.g., 'google', 'outlook')."""
        pass
        
    @abstractmethod
    async def list_events(
        self, 
        user_id: str, 
        time_min: datetime, 
        time_max: datetime
    ) -> List[Dict[str, Any]]:
        """
        List events within a time range.
        
        Args:
            user_id: The user's ID.
            time_min: Start of the time range.
            time_max: End of the time range.
            
        Returns:
            List of event dictionaries.
        """
        pass
        
    @abstractmethod
    async def create_event(
        self,
        user_id: str,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new calendar event.
        
        Args:
            user_id: The user's ID.
            summary: Event title.
            start_time: Event start time.
            end_time: Event end time.
            description: Optional event description.
            location: Optional event location.
            
        Returns:
            Created event details.
        """
        pass
        
    @abstractmethod
    async def check_availability(
        self,
        user_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> bool:
        """
        Check if the user is available during a time slot.
        
        Args:
            user_id: The user's ID.
            start_time: Start of the slot.
            end_time: End of the slot.
            
        Returns:
            True if available, False if busy.
        """
        pass
