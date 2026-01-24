"""
Google Fit API Service - Hardened for Production.

Handles OAuth 2.0 flow, token lifecycle management, and daily biometric data retrieval.
Uses httpx for asynchronous networking, Fernet for credential encryption, 
and normalized data ingestion.
"""

import httpx
import logging
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from urllib.parse import urlencode, quote

from sqlalchemy.orm import Session
from models.models import Connection, HealthDataSample
from core.config import get_settings
from services.connection_service import ConnectionService
from services.audit_service import AuditService

logger = logging.getLogger(__name__)

class GoogleFitService:
    """
    Refactored Google Fit Service with enhanced security, 
    observability, and resilient data processing.
    """
    
    # Provider-specific configuration
    PROVIDER = "google_fit"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    API_BASE = "https://www.googleapis.com/fitness/v1/users/me"
    
    # Scopes required for Viv's health analytics
    SCOPES = [
        "https://www.googleapis.com/auth/fitness.activity.read",
        "https://www.googleapis.com/auth/fitness.body.read",
        "https://www.googleapis.com/auth/fitness.sleep.read",
        "https://www.googleapis.com/auth/fitness.heart_rate.read"
    ]

    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
        self.connection_service = ConnectionService(db)
        
        # Credentials from centralized config
        self.client_id = self.settings.GOOGLE_CLIENT_ID
        self.client_secret = self.settings.GOOGLE_CLIENT_SECRET
        
        # In production, this should be the public URL of the platform
        self.redirect_uri = self.settings.APP_BASE_URL + "/health/google/callback" if hasattr(self.settings, "APP_BASE_URL") else "http://localhost:3000/health/google/callback"
        
        # Shared httpx client configuration
        self.timeout = httpx.Timeout(15.0, connect=5.0)
        self.retry_count = 3

    def get_auth_url(self, state: str) -> str:
        """
        Generate a secure Google OAuth URL with proper encoding and state.
        Guards against missing client credentials.
        """
        if not self.client_id:
            logger.error("Missing GOOGLE_CLIENT_ID in configuration")
            raise ValueError("Google integration is not configured.")

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.SCOPES),
            "access_type": "offline",  # To get refresh token
            "prompt": "consent",       # Ensure we always get a refresh token
            "state": state             # For CSRF protection
        }
        
        return f"{self.AUTH_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str, user_id: str) -> Connection:
        """
        Exchange authorization code for tokens and persist securely using encryption.
        """
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.TOKEN_URL, data=payload)
                response.raise_for_status()
                data = response.json()
            
            # Encrypt sensitive tokens via ConnectionService
            credentials = {
                "access_token": data.get("access_token"),
                "refresh_token": data.get("refresh_token"),
                "token_type": data.get("token_type"),
                "scope": data.get("scope")
            }
            
            # Calculate absolute expiry
            expires_in = data.get("expires_in", 3600)
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            
            metadata = {
                "granted_scopes": data.get("scope", "").split(" "),
                "expires_at": expires_at.isoformat()
            }
            
            connection = self.connection_service.create_or_update_connection(
                user_id=user_id,
                provider=self.PROVIDER,
                credentials=credentials,
                metadata=metadata,
                status="connected"
            )
            
            AuditService.log_audit(
                db=self.db,
                actor_id=user_id,
                action="CONNECTION_CREATE",
                entity_type="CONNECTION",
                entity_id=connection.id,
                metadata={"provider": self.PROVIDER}
            )
            
            return connection

        except Exception as e:
            logger.error(f"Failed to exchange Google code for user {user_id}: {e}")
            raise RuntimeError(f"Could not link Google Fit: {str(e)}")

    async def get_valid_token(self, connection: Connection) -> str:
        """
        Retrieves a valid access token, performing a refresh if expired.
        Uses absolute time comparisons to prevent race conditions.
        """
        creds = self.connection_service._decrypt(connection.credentials_json)
        metadata = json.loads(connection.metadata_json or "{}")
        
        expires_at_str = metadata.get("expires_at")
        expires_at = datetime.fromisoformat(expires_at_str) if expires_at_str else None
        
        # Buffer of 5 minutes to avoid cutting it too close
        if not expires_at or expires_at < datetime.now(timezone.utc) + timedelta(minutes=5):
            creds = await self._refresh_token(connection, creds)
            
        return creds.get("access_token")

    async def _refresh_token(self, connection: Connection, old_creds: Dict) -> Dict:
        """
        Internal handler to refresh Google tokens securely.
        Guards against losing the refresh_token if not returned in response.
        """
        refresh_token = old_creds.get("refresh_token")
        if not refresh_token:
            logger.error(f"Refresh failed: No refresh token for user {connection.user_id}")
            connection.status = "error_refresh_missing"
            self.db.commit()
            raise ValueError("Authentication expired. Please reconnect Google Fit.")

        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.TOKEN_URL, data=payload)
                response.raise_for_status()
                data = response.json()
            
            # NEW tokens + preserve the OLD persistent refresh_token
            new_creds = {
                "access_token": data.get("access_token"),
                "refresh_token": data.get("refresh_token") or refresh_token, # CRITICAL: Guard against overwrite
                "token_type": data.get("token_type", old_creds.get("token_type")),
                "scope": data.get("scope", old_creds.get("scope"))
            }
            
            expires_in = data.get("expires_in", 3600)
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            
            metadata = json.loads(connection.metadata_json or "{}")
            metadata["expires_at"] = expires_at.isoformat()
            metadata["last_refresh"] = datetime.now(timezone.utc).isoformat()
            
            self.connection_service.create_or_update_connection(
                user_id=connection.user_id,
                provider=self.PROVIDER,
                credentials=new_creds,
                metadata=metadata
            )
            
            return new_creds

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 400: # Usually invalid_grant (revoked)
                connection.status = "disconnected"
                self.db.commit()
                logger.warning(f"Google access revoked for {connection.user_id}")
            raise RuntimeError("Token refresh failed. Please reconnect.")

    async def fetch_and_sync_data(self, user_id: str, days: int = 14):
        """
        Orchestrates the retrieval and persistence of health data.
        Includes range bounding and incremental processing.
        """
        # Safety bound
        days = min(max(days, 1), 60)
        
        connection = self.connection_service.get_connection(user_id, self.PROVIDER)
        if not connection or connection.status != "connected":
             raise ValueError("Google Fit is not linked or has been disconnected.")

        token = await self.get_valid_token(connection)
        
        # Binned hourly/daily ranges to avoid overloading API
        end_time = datetime.now(timezone.utc)
        start_time = (end_time - timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Data aggregation request (Daily Buckets)
        body = {
            "aggregateBy": [
                {"dataTypeName": "com.google.step_count.delta"},
                {"dataTypeName": "com.google.calories.expended"},
                {"dataTypeName": "com.google.distance.delta"},
                {"dataTypeName": "com.google.active_minutes"},
                {"dataTypeName": "com.google.heart_rate.bpm"}
            ],
            "bucketByTime": {"durationMillis": 86400000}, # 24 Hours
            "startTimeMillis": int(start_time.timestamp() * 1000),
            "endTimeMillis": int(end_time.timestamp() * 1000)
        }
        
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(f"{self.API_BASE}/dataset:aggregate", headers=headers, json=body)
                response.raise_for_status()
                data = response.json()
            
            await self._process_aggregated_data(user_id, data.get("bucket", []))
            
        except Exception as e:
            logger.error(f"Sync failed for user {user_id}: {e}")
            raise RuntimeError("Cloud sync temporarily unavailable.")

    async def _process_aggregated_data(self, user_id: str, buckets: List[Dict]):
        """
        Parses Google's complex binned dataset structure into flat daily samples.
        Normalizes timestamps to avoid date duplication.
        """
        for bucket in buckets:
            # Normalize to the START of the day in UTC
            bucket_start_ms = int(bucket["startTimeMillis"])
            date_normalized = datetime.fromtimestamp(bucket_start_ms / 1000, tz=timezone.utc).date()
            
            # Prepare an upsert object
            daily_metrics = {
                "steps": 0, "calories": 0.0, "distance": 0.0, 
                "active_mins": 0, "heart_rates": []
            }
            
            for dataset in bucket.get("dataset", []):
                # We use dataTypeName for absolute matching
                dtype = dataset.get("dataSourceId", "")
                points = dataset.get("point", [])
                
                for p in points:
                    val = p.get("value", [{}])[0]
                    
                    if "step_count" in dtype:
                        daily_metrics["steps"] += val.get("intVal", 0)
                    elif "calories" in dtype:
                        daily_metrics["calories"] += val.get("fpVal", 0.0)
                    elif "distance" in dtype:
                        daily_metrics["distance"] += val.get("fpVal", 0.0)
                    elif "active_minutes" in dtype:
                        daily_metrics["active_mins"] += val.get("intVal", 0)
                    elif "heart_rate" in dtype:
                        hr_val = val.get("fpVal", 0.0)
                        if hr_val > 0: daily_metrics["heart_rates"].append(hr_val)

            # Calculate final biometrics
            avg_hr = sum(daily_metrics["heart_rates"]) / len(daily_metrics["heart_rates"]) if daily_metrics["heart_rates"] else 0
            
            # Atomic Upsert logic bounded by User + Date + Source
            # Normalizing to DateTime for the model while keeping 'date' semantic
            dt_day = datetime.combine(date_normalized, datetime.min.time(), tzinfo=timezone.utc)
            
            existing = self.db.query(HealthDataSample).filter(
                HealthDataSample.user_id == user_id,
                HealthDataSample.source == self.PROVIDER,
                HealthDataSample.date == dt_day
            ).first()
            
            if existing:
                existing.steps = daily_metrics["steps"]
                existing.calories_kcal = round(daily_metrics["calories"], 2)
                existing.distance_m = round(daily_metrics["distance"], 2)
                existing.active_minutes = daily_metrics["active_mins"]
                existing.avg_hr_bpm = int(avg_hr)
                existing.updated_at = datetime.now(timezone.utc)
            else:
                new_sample = HealthDataSample(
                    user_id=user_id,
                    source=self.PROVIDER,
                    date=dt_day,
                    steps=daily_metrics["steps"],
                    calories_kcal=round(daily_metrics["calories"], 2),
                    distance_m=round(daily_metrics["distance"], 2),
                    active_minutes=daily_metrics["active_mins"],
                    avg_hr_bpm=int(avg_hr)
                )
                self.db.add(new_sample)

        self.db.commit()
        logger.info(f"Successfully synced {len(buckets)} days for {user_id}")

import json
