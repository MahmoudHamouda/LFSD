import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from models.models import Connection, HealthDataSample
from core.config import get_settings
import logging

logger = logging.getLogger(__name__)

class GoogleFitService:
    """
    Service to handle Google Fit OAuth and Data Fetching.
    """
    
    # Configuration (In production, load from env vars)
    # CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID"
    # CLIENT_SECRET = "YOUR_GOOGLE_CLIENT_SECRET"
    REDIRECT_URI = "http://localhost:3000/health/google/callback" # Frontend route
    
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    API_BASE = "https://www.googleapis.com/fitness/v1/users/me"
    
    SCOPES = [
        "https://www.googleapis.com/auth/fitness.activity.read",
        "https://www.googleapis.com/auth/fitness.body.read",
        "https://www.googleapis.com/auth/fitness.sleep.read",
        "https://www.googleapis.com/auth/fitness.heart_rate.read"
    ]

    def __init__(self, db: Session):
        self.db = db
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
            f"access_type=offline&" # Important for refresh token
            f"prompt=consent&"      # Force consent to get refresh token
            f"state={state}"
        )

    def exchange_code(self, code: str, user_id: str) -> Connection:
        """Exchange auth code for tokens and save connection."""
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
        
        # Save or update connection
        connection = self.db.query(Connection).filter(
            Connection.user_id == user_id,
            Connection.provider == "google_fit"
        ).first()
        
        if not connection:
            connection = Connection(
                user_id=user_id,
                provider="google_fit",
                status="connected"
            )
            self.db.add(connection)
            
        connection.access_token = data.get("access_token")
        connection.refresh_token = data.get("refresh_token") # Only returned on first consent
        connection.token_type = data.get("token_type")
        connection.scope = data.get("scope")
        
        # Calculate expiry
        expires_in = data.get("expires_in", 3600)
        connection.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        connection.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(connection)
        return connection

    def refresh_token(self, connection: Connection):
        """Refresh the access token using the refresh token."""
        if not connection.refresh_token:
            raise Exception("No refresh token available")
            
        payload = {
            "client_id": self.CLIENT_ID,
            "client_secret": self.CLIENT_SECRET,
            "refresh_token": connection.refresh_token,
            "grant_type": "refresh_token"
        }
        
        response = requests.post(self.TOKEN_URL, data=payload)
        if response.status_code != 200:
            # If refresh fails (e.g. revoked), update status
            connection.status = "disconnected"
            self.db.commit()
            raise Exception(f"Failed to refresh token: {response.text}")
            
        data = response.json()
        connection.access_token = data.get("access_token")
        expires_in = data.get("expires_in", 3600)
        connection.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        self.db.commit()

    def get_valid_token(self, connection: Connection) -> str:
        """Get a valid access token, refreshing if necessary."""
        if connection.expires_at and connection.expires_at < datetime.utcnow() + timedelta(minutes=5):
            self.refresh_token(connection)
        return connection.access_token

    def fetch_data(self, user_id: str, days: int = 30):
        """Fetch and normalize data for the last N days."""
        connection = self.db.query(Connection).filter(
            Connection.user_id == user_id,
            Connection.provider == "google_fit"
        ).first()
        
        if not connection or connection.status != "connected":
            raise Exception("Google Fit not connected")
            
        token = self.get_valid_token(connection)
        headers = {"Authorization": f"Bearer {token}"}
        
        # Time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        # Convert to nanoseconds for Google Fit API
        start_nano = int(start_time.timestamp() * 1e9)
        end_nano = int(end_time.timestamp() * 1e9)
        
        # Aggregate Request
        body = {
            "aggregateBy": [
                {"dataTypeName": "com.google.step_count.delta"},
                {"dataTypeName": "com.google.calories.expended"},
                {"dataTypeName": "com.google.distance.delta"},
                {"dataTypeName": "com.google.active_minutes"},
                {"dataTypeName": "com.google.heart_rate.bpm"}
            ],
            "bucketByTime": {"durationMillis": 86400000}, # Daily buckets
            "startTimeMillis": int(start_time.timestamp() * 1000),
            "endTimeMillis": int(end_time.timestamp() * 1000)
        }
        
        response = requests.post(
            f"{self.API_BASE}/dataset:aggregate",
            headers=headers,
            json=body
        )
        
        if response.status_code != 200:
            raise Exception(f"Failed to fetch data: {response.text}")
            
        data = response.json()
        self._process_buckets(user_id, data.get("bucket", []))

    def _process_buckets(self, user_id: str, buckets: List[Dict]):
        """Process daily buckets and save to HealthDataSample."""
        for bucket in buckets:
            start_ms = int(bucket["startTimeMillis"])
            date_obj = datetime.fromtimestamp(start_ms / 1000)
            
            sample = HealthDataSample(
                user_id=user_id,
                source="google_fit",
                date=date_obj,
                steps=0,
                calories_kcal=0,
                distance_m=0,
                active_minutes=0,
                avg_hr_bpm=0
            )
            
            for dataset in bucket["dataset"]:
                point = dataset.get("point", [])
                if not point:
                    continue
                    
                data_type = dataset["dataSourceId"]
                
                # Sum up values in the bucket for this type
                # Note: Google Fit structure is complex, simplified parsing here
                for p in point:
                    val = p["value"][0] # Usually first value is the main one
                    
                    if "step_count" in data_type:
                        sample.steps = (sample.steps or 0) + (val.get("intVal") or 0)
                    elif "calories" in data_type:
                        sample.calories_kcal = (sample.calories_kcal or 0) + (val.get("fpVal") or 0)
                    elif "distance" in data_type:
                        sample.distance_m = (sample.distance_m or 0) + (val.get("fpVal") or 0)
                    elif "active_minutes" in data_type:
                        sample.active_minutes = (sample.active_minutes or 0) + (val.get("intVal") or 0)
                    elif "heart_rate" in data_type:
                        # Average HR logic would be more complex, taking weighted average
                        # Here we just take the last one or average of points if simple
                        sample.avg_hr_bpm = int(val.get("fpVal") or 0)

            # Upsert logic
            existing = self.db.query(HealthDataSample).filter(
                HealthDataSample.user_id == user_id,
                HealthDataSample.source == "google_fit",
                HealthDataSample.date == date_obj
            ).first()
            
            if existing:
                existing.steps = sample.steps
                existing.calories_kcal = sample.calories_kcal
                existing.distance_m = sample.distance_m
                existing.active_minutes = sample.active_minutes
                existing.avg_hr_bpm = sample.avg_hr_bpm
                existing.updated_at = datetime.utcnow()
            else:
                self.db.add(sample)
                
        self.db.commit()
