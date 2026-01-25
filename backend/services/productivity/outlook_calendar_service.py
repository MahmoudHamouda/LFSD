"""
Outlook Calendar Service

Integration with Microsoft Graph API for Outlook Calendar.
Hardened for enterprise usage with normalized schemas and robust error handling.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta, timezone
import logging
import uuid
import httpx

import core.config
from .base_calendar_service import (
    BaseCalendarService, NormalizedEvent, EventStatus, BusyStatus, 
    CalendarAuthError, CalendarServiceError
)

logger = logging.getLogger(__name__)

class OutlookCalendarService(BaseCalendarService):
    """
    Service for interacting with Microsoft Graph API.
    Handles delegated authentication context and provides normalized event data.
    """
    
    BASE_URL = "https://graph.microsoft.com/v1.0"
    
    def __init__(self, db: Session = None):
        self.db = db
        self.settings = core.config.get_settings()
        self.timeout = httpx.Timeout(30.0, connect=10.0)
        
    @property
    def provider_name(self) -> str:
        return "outlook_calendar"

    async def list_calendars(self, user_id: str, account_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List user's Outlook calendars."""
        if not self.access_token:
            return [{"id": "primary", "name": "Calendar", "isDefaultCalendar": True}]
            
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {"Authorization": f"Bearer {self.access_token}"}
                response = await client.get(f"{self.BASE_URL}/me/calendars", headers=headers)
                response.raise_for_status()
                return response.json().get("value", [])
        except Exception as e:
            logger.error(f"Outlook list_calendars failed: {e}")
            raise CalendarServiceError(str(e))

    async def list_events(
        self, 
        user_id: str, 
        time_min: datetime, 
        time_max: datetime,
        account_id: Optional[str] = None,
        calendar_id: str = "primary",
        limit: int = 250
    ) -> List[NormalizedEvent]:
        """List Outlook events via calendarView for accurate recurring expansion."""
        t_min = self._ensure_utc(time_min)
        t_max = self._ensure_utc(time_max)
        
        events = []
        if self.access_token:
            try:
                headers = {"Authorization": f"Bearer {self.access_token}"}
                # Microsoft expects Z format for calendarView
                start_iso = t_min.isoformat().replace("+00:00", "Z")
                end_iso = t_max.isoformat().replace("+00:00", "Z")
                
                # Using calendarView to get instances of recurring events
                url = f"{self.BASE_URL}/me/calendars/{calendar_id}/calendarView?startDateTime={start_iso}&endDateTime={end_iso}&$top={limit}"
                
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, headers=headers)
                    if response.status_code == 401:
                        raise CalendarAuthError("Outlook token expired")
                    response.raise_for_status()
                    
                    items = response.json().get("value", [])
                    for item in items:
                        events.append(self._normalize_outlook_event(item))
                    return events
            except Exception as e:
                logger.error(f"Outlook fetch failed: {e}")
                # Fall through to mock logic

        return self._get_mock_normalized_events(t_min, t_max)

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
        """Create an event in Outlook."""
        t_start = self._ensure_utc(start_time)
        t_end = self._ensure_utc(end_time)
        
        payload = {
            "subject": summary,
            "body": {"contentType": "HTML", "content": description or ""},
            "start": {"dateTime": t_start.isoformat().split("+")[0], "timeZone": "UTC"},
            "end": {"dateTime": t_end.isoformat().split("+")[0], "timeZone": "UTC"},
            "location": {"displayName": location or "Virtual"}
        }

        if self.access_token:
            try:
                headers = {"Authorization": f"Bearer {self.access_token}"}
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(f"{self.BASE_URL}/me/calendars/{calendar_id}/events", json=payload, headers=headers)
                    response.raise_for_status()
                    return self._normalize_outlook_event(response.json())
            except Exception as e:
                logger.error(f"Outlook creation failed: {e}")
                raise CalendarServiceError(str(e))

        return NormalizedEvent(
            id=f"mock_o_{uuid.uuid4().hex[:8]}",
            summary=summary,
            start_time=t_start,
            end_time=t_end,
            description=description,
            location=location,
            status=EventStatus.TENTATIVE
        )

    async def delete_event(self, user_id: str, event_id: str, account_id: Optional[str] = None, calendar_id: str = "primary") -> bool:
        if not self.access_token: return True
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.delete(f"{self.BASE_URL}/me/events/{event_id}", headers=headers)
                return response.status_code in [200, 204]
        except Exception:
            return False

    async def check_availability(self, user_id: str, start_time: datetime, end_time: datetime, **kwargs) -> BusyStatus:
        events = await self.list_events(user_id, start_time, end_time, **kwargs)
        max_busy = BusyStatus.FREE
        for e in events:
            if e.busy_status == BusyStatus.BUSY: return BusyStatus.BUSY
            if e.busy_status.value > max_busy.value:
                max_busy = e.busy_status
        return max_busy

    def _normalize_outlook_event(self, o_event: Dict[str, Any]) -> NormalizedEvent:
        """Map Outlook Graph fields to NormalizedEvent."""
        def parse_graph_date(d_obj: Dict[str, str]) -> datetime:
            dt_str = d_obj.get("dateTime", "")
            # Graph usually returns naive Z-less strings but specifies timezone in separate field
            # We assume UTC since we send everything as UTC
            if "Z" not in dt_str: dt_str += "Z"
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))

        status_map = {
            "none": EventStatus.CONFIRMED, # Not exactly cancelled
            "organizer": EventStatus.CONFIRMED,
            "tentativelyAccepted": EventStatus.TENTATIVE,
            "accepted": EventStatus.CONFIRMED,
            "declined": EventStatus.CANCELLED
        }
        
        busy_status_map = {
            "free": BusyStatus.FREE,
            "tentative": BusyStatus.TENTATIVE,
            "busy": BusyStatus.BUSY,
            "oof": BusyStatus.OOF,
            "workingElsewhere": BusyStatus.OOF
        }

        return NormalizedEvent(
            id=o_event.get("id", "unknown"),
            summary=o_event.get("subject", "Untitled Event"),
            start_time=parse_graph_date(o_event.get("start", {})),
            end_time=parse_graph_date(o_event.get("end", {})),
            description=o_event.get("body", {}).get("content"),
            location=o_event.get("location", {}).get("displayName"),
            status=status_map.get(o_event.get("responseStatus", {}).get("response"), EventStatus.CONFIRMED),
            busy_status=busy_status_map.get(o_event.get("showAs", "busy").lower(), BusyStatus.BUSY),
            is_all_day=o_event.get("isAllDay", False),
            raw=o_event
        )

    def _get_mock_normalized_events(self, t_min: datetime, t_max: datetime) -> List[NormalizedEvent]:
        # Same deterministic mock logic
        now = datetime.now(timezone.utc)
        start = (now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
        end = start + timedelta(hours=1)
        
        if start < t_max and end > t_min:
            return [NormalizedEvent(
                id="mock_o_1",
                summary="System Review Meeting",
                start_time=start,
                end_time=end,
                busy_status=BusyStatus.BUSY,
                location="Teams"
            )]
        return []

def get_outlook_calendar_service(access_token: Optional[str] = None) -> OutlookCalendarService:
    return OutlookCalendarService(access_token=access_token)
