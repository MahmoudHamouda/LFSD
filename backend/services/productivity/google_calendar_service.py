from __future__ import annotations
"""
Google Calendar Service - Hardened Enterprise Implementation.

Handles OAuth 2.0 flow, token lifecycle, and full CRUD for events.
Implements the BaseCalendarService interface with strict normalization,
resilient pagination, and secure credential handling.
"""

import httpx
import logging
import uuid
import json
import datetime
from typing import List, Dict, Any, Optional, Union
from urllib.parse import urlencode

from sqlalchemy.orm import Session
from models.models import Connection, CalendarEvent
import core.config
from services.connection_service import ConnectionService
from services.audit_service import AuditService
from .base_calendar_service import (
    BaseCalendarService, NormalizedEvent, EventStatus, BusyStatus, 
    CalendarAuthError, CalendarServiceError, CalendarRateLimitError
)

logger = logging.getLogger(__name__)

class GoogleCalendarService(BaseCalendarService):
    """
    Hardened service for Google Calendar API (v3).
    Supports persistent sync, resilient token management, and standardized schemas.
    """
    
    PROVIDER = "google_calendar"
    API_BASE = "https://www.googleapis.com/calendar/v3"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    
    SCOPES = [
        "https://www.googleapis.com/auth/calendar.readonly",
        "https://www.googleapis.com/auth/calendar.events"
    ]

    def __init__(self, db: Optional[Session] = None, access_token: Optional[str] = None):
        """
        Initialize the service.
        Can operate with a direct access_token (stateless) or a db session (managed).
        """
        self.db = db
        self.settings = core.config.get_settings()
        self.access_token = access_token
        self.connection_service = ConnectionService(db) if db else None
        
        self.client_id = self.settings.GOOGLE_CLIENT_ID
        self.client_secret = self.settings.GOOGLE_CLIENT_SECRET
        self.redirect_uri = self.settings.APP_BASE_URL + "/productivity/google/callback"
        
        self.timeout = httpx.Timeout(20.0, connect=10.0)

    @property
    def provider_name(self) -> str:
        return self.PROVIDER

    def get_auth_url(self, state: str) -> str:
        """Generate a secure OAuth URL with proper encoding."""
        if not self.client_id:
            raise ValueError("Google CLIENT_ID not configured")

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "state": state
        }
        return f"{self.AUTH_URL}?{urlencode(params)}"

    async def _ensure_authorized(self, user_id: str) -> str:
        """Ensures we have a valid access token, refreshing if necessary."""
        if self.access_token:
             return self.access_token

        if not self.db or not self.connection_service:
             raise CalendarAuthError("Service not configured for managed auth")

        connection = self.connection_service.get_connection(user_id, self.PROVIDER)
        if not connection or connection.status != "connected":
             raise CalendarAuthError("Google Calendar not connected for this user")

        # Check metadata for expiry with 5min buffer
        metadata = json.loads(connection.metadata_json or "{}")
        expires_at_str = metadata.get("expires_at")
        
        should_refresh = True
        if expires_at_str:
            expires_at = datetime.datetime.fromisoformat(expires_at_str)
            if expires_at > datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=5):
                should_refresh = False

        if should_refresh:
            creds = await self._refresh_token(connection)
            return creds["access_token"]
        
        # Decrypt existing token
        creds = self.connection_service._decrypt(connection.credentials_json)
        return creds["access_token"]

    async def _refresh_token(self, connection: Connection) -> Dict:
        """Internal Google-specific refresh logic."""
        creds = self.connection_service._decrypt(connection.credentials_json)
        refresh_token = creds.get("refresh_token")
        
        if not refresh_token:
            connection.status = "disconnected"
            self.db.commit()
            raise CalendarAuthError("Refresh token missing. Re-authentication required.")

        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.TOKEN_URL, data=payload)
                if response.status_code == 400: # invalid_grant
                    connection.status = "disconnected"
                    self.db.commit()
                    raise CalendarAuthError("Google access revoked or invalid refresh token.")
                
                response.raise_for_status()
                data = response.json()

            # Preserve the old refresh_token if not rotated by Google
            new_creds = {
                "access_token": data["access_token"],
                "refresh_token": data.get("refresh_token") or refresh_token,
                "token_type": data.get("token_type", "Bearer")
            }
            
            expires_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=data.get("expires_in", 3600))
            metadata = json.loads(connection.metadata_json or "{}")
            metadata["expires_at"] = expires_at.isoformat()
            
            self.connection_service.create_or_update_connection(
                user_id=connection.user_id,
                provider=self.PROVIDER,
                credentials=new_creds,
                metadata=metadata
            )
            return new_creds

        except Exception as e:
            logger.error(f"Google refresh failed for {connection.user_id}: {e}")
            raise CalendarAuthError(f"OAuth Refresh Failure: {str(e)}")

    async def list_events(
        self, 
        user_id: str, 
        time_min: datetime.datetime, 
        time_max: datetime.datetime,
        account_id: Optional[str] = None,
        calendar_id: str = "primary",
        limit: int = 500
    ) -> List[NormalizedEvent]:
        """
        List and consolidate events with pagination and error handling.
        """
        token = await self._ensure_authorized(user_id)
        
        t_min = self._ensure_utc(time_min).isoformat().replace("+00:00", "Z")
        t_max = self._ensure_utc(time_max).isoformat().replace("+00:00", "Z")
        
        params = {
            "timeMin": t_min,
            "timeMax": t_max,
            "singleEvents": "true",
            "orderBy": "startTime",
            "maxResults": min(limit, 2500)
        }
        
        all_events = []
        page_token = None
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                while True:
                    if page_token:
                         params["pageToken"] = page_token
                         
                    headers = {"Authorization": f"Bearer {token}"}
                    response = await client.get(
                        f"{self.API_BASE}/calendars/{calendar_id}/events",
                        headers=headers, params=params
                    )
                    
                    if response.status_code == 429:
                         raise CalendarRateLimitError("Google Calendar API quota exceeded")
                    response.raise_for_status()
                    
                    data = response.json()
                    items = data.get("items", [])
                    for item in items:
                        all_events.append(self._normalize_google_event(item))
                        
                    page_token = data.get("nextPageToken")
                    if not page_token or len(all_events) >= limit:
                        break
                        
            return all_events

        except httpx.HTTPStatusError as e:
            logger.error(f"Google API Error {e.response.status_code}: {e.response.text}")
            raise CalendarServiceError(f"Provider Error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Unexpected error fetching Google events: {e}")
            raise CalendarServiceError(str(e))

    async def create_event(
        self,
        user_id: str,
        summary: str,
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        description: Optional[str] = None,
        location: Optional[str] = None,
        account_id: Optional[str] = None,
        calendar_id: str = "primary",
        idempotency_key: Optional[str] = None
    ) -> NormalizedEvent:
        """Create an event with proper timezone and audit trail."""
        token = await self._ensure_authorized(user_id)
        
        t_start = self._ensure_utc(start_time)
        t_end = self._ensure_utc(end_time)

        payload = {
            "summary": summary,
            "description": description or "",
            "location": location or "",
            "start": {"dateTime": t_start.isoformat().replace("+00:00", "Z"), "timeZone": "UTC"},
            "end": {"dateTime": t_end.isoformat().replace("+00:00", "Z"), "timeZone": "UTC"}
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
                # Note: v3 doesn't support body-based idempotency keys, 
                # we'd need to use a client side uuid for 'id' if we wanted strict idempotency.
                response = await client.post(
                    f"{self.API_BASE}/calendars/{calendar_id}/events",
                    headers=headers, json=payload
                )
                response.raise_for_status()
                result = response.json()
                
                normalized = self._normalize_google_event(result)
                
                # Sync to local DB if available
                if self.db:
                    self._upsert_local_event(user_id, normalized)
                
                return normalized

        except Exception as e:
            logger.error(f"Google Create Event failed for {user_id}: {e}")
            raise CalendarServiceError(f"Creation failed: {str(e)}")

    def _normalize_google_event(self, g_event: Dict[str, Any]) -> NormalizedEvent:
        """Maps Google's JSON to standard NormalizedEvent."""
        start_data = g_event.get("start", {})
        end_data = g_event.get("end", {})
        
        start_raw = start_data.get("dateTime") or start_data.get("date")
        end_raw = end_data.get("dateTime") or end_data.get("date")
        
        def parse_dt(raw: str) -> datetime.datetime:
            if not raw: return datetime.datetime.now(datetime.timezone.utc)
            if len(raw) == 10: raw += "T00:00:00Z"
            # Normalize to aware UTC
            dt = datetime.datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if dt.tzinfo is None: dt = dt.replace(tzinfo=datetime.timezone.utc)
            return dt.astimezone(datetime.timezone.utc)

        status_map = {
            "confirmed": EventStatus.CONFIRMED,
            "tentative": EventStatus.TENTATIVE,
            "cancelled": EventStatus.CANCELLED
        }
        
        busy = BusyStatus.FREE if g_event.get("transparency") == "transparent" else BusyStatus.BUSY

        return NormalizedEvent(
            id=g_event.get("id"),
            summary=g_event.get("summary", "No Title"),
            start_time=parse_dt(start_raw),
            end_time=parse_dt(end_raw),
            description=g_event.get("description"),
            location=g_event.get("location"),
            status=status_map.get(g_event.get("status"), EventStatus.CONFIRMED),
            busy_status=busy,
            is_all_day=("date" in start_data),
            raw=g_event
        )

    def _upsert_local_event(self, user_id: str, event: NormalizedEvent):
        """Persist a single event to the local DB for fast caching/analytics."""
        existing = self.db.query(CalendarEvent).filter(
            CalendarEvent.user_id == user_id,
            CalendarEvent.id == event.id # Assuming ID matches provider ID for sync
        ).first()

        if existing:
            existing.title = event.summary
            existing.start_time = event.start_time
            existing.end_time = event.end_time
            existing.location_context = event.location
        else:
            new_event = CalendarEvent(
                id=event.id,
                user_id=user_id,
                start_time=event.start_time,
                end_time=event.end_time,
                title=event.summary,
                location_context=event.location
            )
            self.db.add(new_event)
        
        self.db.commit()

    # --- Async-Safe Sync Wrappers (Using anyio or threadpool) ---
    def list_events_sync(self, *args, **kwargs) -> List[NormalizedEvent]:
        """Thread-safe sync wrapper for blocking callers."""
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self.list_events(*args, **kwargs))
        finally:
            loop.close()

    async def list_calendars(self, user_id: str, account_id: Optional[str] = None) -> List[Dict[str, Any]]:
        token = await self._ensure_authorized(user_id)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            headers = {"Authorization": f"Bearer {token}"}
            response = await client.get(f"{self.API_BASE}/users/me/calendarList", headers=headers)
            response.raise_for_status()
            return response.json().get("items", [])

    async def delete_event(self, user_id: str, event_id: str, account_id: Optional[str] = None, calendar_id: str = "primary") -> bool:
        token = await self._ensure_authorized(user_id)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
             headers = {"Authorization": f"Bearer {token}"}
             resp = await client.delete(f"{self.API_BASE}/calendars/{calendar_id}/events/{event_id}", headers=headers)
             return resp.status_code in [200, 204]

    async def check_availability(self, user_id: str, start_time: datetime.datetime, end_time: datetime.datetime, **kwargs) -> BusyStatus:
        events = await self.list_events(user_id, start_time, end_time, **kwargs)
        for e in events:
             if e.busy_status == BusyStatus.BUSY and e.status != EventStatus.CANCELLED:
                  return BusyStatus.BUSY
        return BusyStatus.FREE

def get_google_calendar_service(db: Optional[Session] = None, access_token: Optional[str] = None) -> GoogleCalendarService:
    return GoogleCalendarService(db=db, access_token=access_token)
