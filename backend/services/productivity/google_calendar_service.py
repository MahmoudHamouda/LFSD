"""
Google Calendar Service

Integration with Google Calendar API.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from core.config import get_settings
from .base_calendar_service import BaseCalendarService
import logging
import uuid

logger = logging.getLogger(__name__)

class GoogleCalendarService(BaseCalendarService):
    """Service for interacting with Google Calendar API."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client_id = self.settings.GOOGLE_CLIENT_ID
        self.client_secret = self.settings.GOOGLE_CLIENT_SECRET
        
    @property
    def provider_name(self) -> str:
        return "google"
        
    async def list_events(
        self, 
        user_id: str, 
        time_min: datetime, 
        time_max: datetime
    ) -> List[Dict[str, Any]]:
        """List events from Google Calendar."""
        if not self.client_id:
            logger.warning("Google Calendar credentials not configured. Returning mock events.")
            return self._get_mock_events(time_min, time_max)
            
        # TODO: Implement actual Google Calendar API call
        # This requires OAuth flow which is complex to implement without frontend interaction
        # For now, we'll simulate the API response structure
        return self._get_mock_events(time_min, time_max)

    async def create_event(
        self,
        user_id: str,
        summary: str,
        start_time: datetime,
        end_time: datetime,
        description: Optional[str] = None,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new event in Google Calendar."""
        if not self.client_id:
            logger.warning("Google Calendar credentials not configured. Returning mock event.")
            return {
                "id": f"mock_event_{uuid.uuid4()}",
                "summary": summary,
                "start": {"dateTime": start_time.isoformat()},
                "end": {"dateTime": end_time.isoformat()},
                "description": description,
                "location": location,
                "status": "confirmed",
                "htmlLink": "https://calendar.google.com/mock_event"
            }
            
        # TODO: Implement actual Google Calendar API call
        return {
            "id": f"gcal_{uuid.uuid4()}",
            "summary": summary,
            "start": {"dateTime": start_time.isoformat()},
            "end": {"dateTime": end_time.isoformat()},
            "description": description,
            "location": location,
            "status": "confirmed",
            "htmlLink": "https://calendar.google.com/event"
        }

    async def check_availability(
        self,
        user_id: str,
        start_time: datetime,
        end_time: datetime
    ) -> bool:
        """Check availability."""
        events = await self.list_events(user_id, start_time, end_time)
        return len(events) == 0

    def _get_mock_events(self, time_min: datetime, time_max: datetime) -> List[Dict[str, Any]]:
        """Generate realistic mock events."""
        events = []
        
        # Add a "Team Meeting" tomorrow at 10am
        tomorrow = datetime.now() + timedelta(days=1)
        start = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
        end = start + timedelta(hours=1)
        
        if time_min <= start <= time_max:
            events.append({
                "id": "mock_evt_1",
                "summary": "Team Sync",
                "start": {"dateTime": start.isoformat()},
                "end": {"dateTime": end.isoformat()},
                "location": "Conference Room A",
                "description": "Weekly team sync"
            })
            
        # Add a "Lunch" today at 1pm
        today = datetime.now()
        start_lunch = today.replace(hour=13, minute=0, second=0, microsecond=0)
        end_lunch = start_lunch + timedelta(hours=1)
        
        if time_min <= start_lunch <= time_max:
            events.append({
                "id": "mock_evt_2",
                "summary": "Lunch with Client",
                "start": {"dateTime": start_lunch.isoformat()},
                "end": {"dateTime": end_lunch.isoformat()},
                "location": "Zuma Dubai",
                "description": "Discuss project proposal"
            })
            
        return events

# Singleton instance
_google_calendar_service = None

def get_google_calendar_service() -> GoogleCalendarService:
    """Get or create the Google Calendar service singleton."""
    global _google_calendar_service
    if _google_calendar_service is None:
        _google_calendar_service = GoogleCalendarService()
    return _google_calendar_service
