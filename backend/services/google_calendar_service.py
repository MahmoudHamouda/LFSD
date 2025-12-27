import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from models.models import Connection, CalendarEvent
from core.config import get_settings
import logging

logger = logging.getLogger(__name__)

class GoogleCalendarService:
    """
    Service to handle Google Calendar OAuth and Data Fetching.
    """
    
    REDIRECT_URI = "http://localhost:3000/productivity/google/callback"
    
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    API_BASE = "https://www.googleapis.com/calendar/v3"
    
    SCOPES = [
        "https://www.googleapis.com/auth/calendar.readonly",
        "https://www.googleapis.com/auth/calendar.events.readonly"
    ]

    def __init__(self, db: Session, user_id: Optional[str] = None):
        self.db = db
        self.user_id = user_id
        self.settings = get_settings()
        self.CLIENT_ID = self.settings.GOOGLE_CLIENT_ID
        self.CLIENT_SECRET = self.settings.GOOGLE_CLIENT_SECRET

    def get_auth_url(self, state: str = "") -> str:
        """Generate the Google OAuth URL."""
        scope_str = " ".join(self.SCOPES)
        return (
            f"{self.AUTH_URL}?"
            f"client_id={self.CLIENT_ID}&"
            f"redirect_uri={self.REDIRECT_URI}&"
            f"response_type=code&"
            f"scope={scope_str}&"
            f"access_type=offline&"
            f"prompt=consent&"
            f"state={state}"
        )

    def exchange_code(self, code: str, user_id: str) -> Connection:
        """Exchange auth code for tokens."""
        payload = {
            "client_id": self.CLIENT_ID,
            "client_secret": self.CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.REDIRECT_URI
        }
        
        response = requests.post(self.TOKEN_URL, data=payload)
        if response.status_code != 200:
            raise Exception(f"Failed to exchange code: {response.text}")
            
        data = response.json()
        
        connection = self.db.query(Connection).filter(
            Connection.user_id == user_id,
            Connection.provider == "google_calendar"
        ).first()
        
        if not connection:
            connection = Connection(
                user_id=user_id,
                provider="google_calendar",
                status="connected"
            )
            self.db.add(connection)
            
        connection.access_token = data.get("access_token")
        connection.refresh_token = data.get("refresh_token")
        connection.token_type = data.get("token_type")
        connection.scope = data.get("scope")
        
        expires_in = data.get("expires_in", 3600)
        connection.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        connection.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(connection)
        return connection

    def fetch_events(self, user_id: str, days: int = 30):
        """Fetch calendar events."""
        connection = self.db.query(Connection).filter(
            Connection.user_id == user_id,
            Connection.provider == "google_calendar"
        ).first()
        
        if not connection or connection.status != "connected":
            raise Exception("Google Calendar not connected")
            
        # TODO: Implement token refresh logic here (shared with Fit service ideally)
        token = connection.access_token 
        headers = {"Authorization": f"Bearer {token}"}
        
        now = datetime.utcnow()
        time_min = now.isoformat() + "Z"
        time_max = (now + timedelta(days=days)).isoformat() + "Z"
        
        # List events from primary calendar
        response = requests.get(
            f"{self.API_BASE}/calendars/primary/events",
            headers=headers,
            params={
                "timeMin": time_min,
                "timeMax": time_max,
                "singleEvents": True,
                "orderBy": "startTime"
            }
        )
        
        if response.status_code != 200:
             # If 401, refresh token and retry (omitted for brevity)
            raise Exception(f"Failed to fetch events: {response.text}")
            
        data = response.json()
        items = data.get("items", [])
        
        for item in items:
            # Parse start/end
            start = item.get("start", {}).get("dateTime") or item.get("start", {}).get("date")
            end = item.get("end", {}).get("dateTime") or item.get("end", {}).get("date")
            
            # Simple parsing (ignoring all-day events logic for now)
            if not start or not end:
                continue
                
            # Upsert logic would go here
            # For now, we just log or store in DB
            pass
            
        return len(items)

    def get_events(self, user_id: str, time_min: str, time_max: str) -> List[Dict[str, Any]]:
        """Fetch events for a specific time range."""
        connection = self.db.query(Connection).filter(
            Connection.user_id == user_id,
            Connection.provider == "google_calendar"
        ).first()

        if not connection or connection.status != "connected":
            # For now, if not connected, return empty list or raise?
            # Creating a mock event if not connected to allow testing locally without real auth
            return []

        token = connection.access_token 
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.get(
            f"{self.API_BASE}/calendars/primary/events",
            headers=headers,
            params={
                "timeMin": time_min,
                "timeMax": time_max,
                "singleEvents": True,
                "orderBy": "startTime"
            }
        )
        
        if response.status_code != 200:
             return []
             
        data = response.json()
        return data.get("items", [])

    def create_event(self, user_id: str, summary: str, start_time: str, end_time: str) -> Dict[str, Any]:
        """Create a new event."""
        connection = self.db.query(Connection).filter(
            Connection.user_id == user_id,
            Connection.provider == "google_calendar"
        ).first()
        
        if not connection or connection.status != "connected":
            # Mock creation if not connected
            return {"id": "mock_event_id", "summary": summary, "status": "mock_confirmed"}

        token = connection.access_token
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "summary": summary,
            "start": {"dateTime": start_time},
            "end": {"dateTime": end_time}
        }
        
        response = requests.post(
            f"{self.API_BASE}/calendars/primary/events",
            headers=headers,
            json=payload
        )
        
        if response.status_code not in [200, 201]:
             raise Exception(f"Failed to create event: {response.text}")
             
        return response.json()

    def creds_to_json(self, creds) -> Dict[str, Any]:
        """Convert Credentials object to dict."""
        return {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": creds.scopes
        }
