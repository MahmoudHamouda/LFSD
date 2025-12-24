"""
Outlook Calendar Service

Integration with Microsoft Graph API for Outlook Calendar.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from core.config import get_settings
from .base_calendar_service import BaseCalendarService
import logging
import uuid
import httpx

logger = logging.getLogger(__name__)

class OutlookCalendarService(BaseCalendarService):
    """Service for interacting with Microsoft Graph API."""
    
    BASE_URL = "https://graph.microsoft.com/v1.0"
    
    def __init__(self):
        self.settings = get_settings()
        self.client_id = self.settings.MICROSOFT_CLIENT_ID
        self.client_secret = self.settings.MICROSOFT_CLIENT_SECRET
        self.tenant_id = self.settings.MICROSOFT_TENANT_ID
        
    @property
    def provider_name(self) -> str:
        return "outlook"
        
    async def list_events(
        self, 
        user_id: str, 
        time_min: datetime, 
        time_max: datetime
    ) -> List[Dict[str, Any]]:
        """List events from Outlook Calendar."""
        if not self.client_id:
            logger.warning("Microsoft Graph credentials not configured. Returning mock events.")
            return self._get_mock_events(time_min, time_max)
            
        # TODO: Implement actual Microsoft Graph API call
        # Requires OAuth token acquisition
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
        """Create a new event in Outlook Calendar."""
        if not self.client_id:
            logger.warning("Microsoft Graph credentials not configured. Returning mock event.")
            return {
                "id": f"mock_outlook_{uuid.uuid4()}",
                "subject": summary,
                "start": {"dateTime": start_time.isoformat(), "timeZone": "UTC"},
                "end": {"dateTime": end_time.isoformat(), "timeZone": "UTC"},
                "body": {"content": description, "contentType": "text"},
                "location": {"displayName": location},
                "webLink": "https://outlook.office.com/calendar/mock_event"
            }
            
        # TODO: Implement actual Microsoft Graph API call
        return {
            "id": f"outlook_{uuid.uuid4()}",
            "subject": summary,
            "start": {"dateTime": start_time.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": end_time.isoformat(), "timeZone": "UTC"},
            "body": {"content": description, "contentType": "text"},
            "location": {"displayName": location},
            "webLink": "https://outlook.office.com/calendar/event"
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
        """Generate realistic mock events for Outlook."""
        events = []
        
        # Add a "Project Review" tomorrow at 3pm
        tomorrow = datetime.now() + timedelta(days=1)
        start = tomorrow.replace(hour=15, minute=0, second=0, microsecond=0)
        end = start + timedelta(hours=1)
        
        if time_min <= start <= time_max:
            events.append({
                "id": "mock_outlook_1",
                "subject": "Project Review Board",
                "start": {"dateTime": start.isoformat(), "timeZone": "UTC"},
                "end": {"dateTime": end.isoformat(), "timeZone": "UTC"},
                "location": {"displayName": "Teams Meeting"},
                "body": {"content": "Review Q4 roadmap", "contentType": "text"},
                "organizer": {"emailAddress": {"name": "Manager", "address": "manager@company.com"}}
            })
            
        return events

# Singleton instance
_outlook_calendar_service = None

def get_outlook_calendar_service() -> OutlookCalendarService:
    """Get or create the Outlook Calendar service singleton."""
    global _outlook_calendar_service
    if _outlook_calendar_service is None:
        _outlook_calendar_service = OutlookCalendarService()
    return _outlook_calendar_service
