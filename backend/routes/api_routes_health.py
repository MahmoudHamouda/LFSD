"""
Health API Routes

Endpoints for managing health provider connections and syncing health metrics.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import uuid
from models.database import get_db
from models.models import Connection, HealthDailySummary, SleepSession, Workout
from services.health_service import HealthService
from core.authentication import get_current_user
from models.models import User

router = APIRouter(prefix="/api/health", tags=["health"])

# Pydantic Models
# ============================================================================

class ConnectHealthProviderRequest(BaseModel):
    provider: str  # "whoop", "apple_health", "android_health"
    authCode: Optional[str] = None
    permissions: List[str]

class ConnectHealthProviderResponse(BaseModel):
    connection: dict
    redirectUrl: Optional[str] = None

class DisconnectHealthProviderRequest(BaseModel):
    provider: str

class SyncHealthMetricsRequest(BaseModel):
    provider: str
    startDate: Optional[str] = None
    endDate: Optional[str] = None

class HealthMetricData(BaseModel):
    metricType: str
    value: float
    timestamp: str
    provider: str
    rawData: Optional[dict] = None

class SyncHealthMetricsResponse(BaseModel):
    metrics: List[HealthMetricData]
    syncedAt: str
    nextSyncAt: Optional[str] = None

# ============================================================================
# Helper Functions
# ============================================================================

def create_health_connection(user_id: str, provider: str, permissions: List[str], db: Session):
    """Create a new health connection record."""
    connection = Connection(
        id=str(uuid.uuid4()),
        user_id=user_id,
        provider=provider,
        status="connecting",
        metadata_json=json.dumps({"permissions": permissions}),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(connection)
    db.commit()
    db.refresh(connection)
    return connection

def update_connection_status(connection_id: str, status: str, db: Session, error_message: Optional[str] = None):
    """Update health connection status."""
    connection = db.query(Connection).filter(Connection.id == connection_id).first()
    if connection:
        connection.status = status
        connection.updated_at = datetime.utcnow()
        if error_message:
            meta = json.loads(connection.metadata_json or "{}")
            meta["last_error"] = error_message
            connection.metadata_json = json.dumps(meta)
            
        db.commit()

def store_health_metric(user_id: str, provider: str, metric_type: str, value: float, timestamp: datetime, raw_data: Optional[dict], db: Session):
    """Store a health metric into appropriate table."""
    
    # 1. Sleep -> SleepSession (Simplified mapping)
    if metric_type == "sleep":
        session = SleepSession(
            id=str(uuid.uuid4()),
            user_id=user_id,
            start_time=timestamp, # Approximation
            end_time=timestamp,   # Approximation
            deep_sleep_minutes=int(value * 0.2), # Mock breakdown
            rem_sleep_minutes=int(value * 0.25),
            wake_count=2
        )
        db.add(session)
        
    # 2. Activity -> Workout
    elif metric_type == "activity":
        workout = Workout(
            id=str(uuid.uuid4()),
            user_id=user_id,
            start_time=timestamp,
            end_time=timestamp,
            activity_type="General",
            calories_burned=int(value * 10), # Mock
            average_heart_rate=120,
            perceived_exertion=5.0
        )
        db.add(workout)
        
    # 3. Recovery/HRV -> HealthDailySummary
    elif metric_type in ["recovery", "hrv"]:
        date = timestamp.date()
        summary = db.query(HealthDailySummary).filter(
            HealthDailySummary.user_id == user_id,
            HealthDailySummary.date == date
        ).first()
        
        if not summary:
            summary = HealthDailySummary(
                id=str(uuid.uuid4()),
                user_id=user_id,
                date=date
            )
            db.add(summary)
        
        if metric_type == "recovery":
            pass 
        elif metric_type == "hrv":
            summary.hrv_average = value
            
    db.commit()

# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/connections")
async def get_health_connections(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all health provider connections for the current user.
    """
    user_id = current_user.id
    
    health_providers = ["whoop", "apple_health", "android_health"]
    connections = db.query(Connection).filter(
        Connection.user_id == user_id,
        Connection.provider.in_(health_providers)
    ).all()
    
    return {
        "connections": [
            {
                "id": conn.id,
                "provider": conn.provider,
                "status": conn.status,
                "permissions": json.loads(conn.metadata_json).get("permissions", []) if conn.metadata_json else [],
                "connectedAt": conn.updated_at.isoformat() if conn.status == "connected" else None,
                "lastSyncedAt": conn.updated_at.isoformat(),
                "errorMessage": json.loads(conn.metadata_json or "{}").get("last_error")
            }
            for conn in connections
        ]
    }

@router.post("/connections")
async def connect_health_provider(
    request: ConnectHealthProviderRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initiate connection to a health provider.
    """
    user_id = current_user.id
    
    existing = db.query(Connection).filter(
        Connection.user_id == user_id,
        Connection.provider == request.provider
    ).first()
    
    if existing and existing.status == "connected":
        raise HTTPException(status_code=400, detail="Provider already connected")
    
    if existing:
        existing.status = "connecting"
        meta = json.loads(existing.metadata_json or "{}")
        meta["permissions"] = request.permissions
        existing.metadata_json = json.dumps(meta)
        existing.updated_at = datetime.utcnow()
        db.commit()
        connection = existing
    else:
        connection = create_health_connection(user_id, request.provider, request.permissions, db)
    
    if request.provider == "whoop":
        import core.config
        settings = core.config.get_settings()
        redirect_url = f"https://api.whoop.com/oauth/authorize?client_id={settings.WHOOP_CLIENT_ID}&redirect_uri={settings.WHOOP_REDIRECT_URI}&scope={','.join(request.permissions)}"
        
        return ConnectHealthProviderResponse(
            connection={
                "id": connection.id,
                "provider": connection.provider,
                "status": connection.status
            },
            redirectUrl=redirect_url
        )
    
    elif request.provider in ["apple_health", "android_health"]:
        update_connection_status(connection.id, "connected", db)
        
        # Trigger mock data sync to simulate pulling data
        service = HealthService(db)
        service.sync_mock_data(user_id)
        
        return ConnectHealthProviderResponse(
            connection={
                "id": connection.id,
                "provider": connection.provider,
                "status": "connected"
            }
        )
    
    raise HTTPException(status_code=400, detail="Unsupported provider")

# ============================================================================
# Google Fit & Apple Health Routes
# ============================================================================

@router.post("/google/auth-url")
async def get_google_auth_url(db: Session = Depends(get_db)):
    from services.google_fit_service import GoogleFitService
    import secrets
    service = GoogleFitService(db)
    # Generate a random state for security in prod
    state = secrets.token_urlsafe(16)
    return {"url": service.get_auth_url(state=state)}

@router.post("/google/callback")
async def google_auth_callback(
    payload: dict, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Exchange code for token."""
    code = payload.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")
        
    from services.google_fit_service import GoogleFitService
    service = GoogleFitService(db)
    try:
        connection = service.exchange_code(code, current_user.id)
        # Initial sync
        service.fetch_data(current_user.id, days=30)
        return {"status": "connected", "provider": "google_fit"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/apple/auth-url")
async def get_apple_auth_url(db: Session = Depends(get_db)):
    from services.integrations.apple_health_service import AppleHealthService
    import secrets
    service = AppleHealthService(db)
    state = secrets.token_urlsafe(16)
    return {"url": service.get_auth_url(state=state)}

@router.post("/apple/callback")
async def apple_auth_callback(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Exchange code for token (Sign in with Apple)."""
    code = payload.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")
        
    from services.integrations.apple_health_service import AppleHealthService
    service = AppleHealthService(db)
    try:
        connection = service.exchange_code(code, current_user.id)
        # Trigger data fetch (simulated/middleware)
        service.fetch_data(current_user.id, days=30)
        return {"status": "connected", "provider": "apple_health"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/connections/{provider}")
async def disconnect_health_provider(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Disconnect a health provider.
    """
    user_id = current_user.id
    
    connection = db.query(Connection).filter(
        Connection.user_id == user_id,
        Connection.provider == provider
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    db.delete(connection)
    db.commit()
    
    return {"message": f"Disconnected from {provider}"}

@router.get("/summaries", summary="Get recent health summaries")
async def get_health_summaries(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of daily health summaries.
    """
    query = db.query(HealthDailySummary).filter(HealthDailySummary.user_id == current_user.id)
    
    if start_date:
        query = query.filter(HealthDailySummary.date >= datetime.strptime(start_date, "%Y-%m-%d").date())
    if end_date:
        query = query.filter(HealthDailySummary.date <= datetime.strptime(end_date, "%Y-%m-%d").date())
        
    # Default to last 30 days if no date range
    if not start_date and not end_date:
        query = query.order_by(HealthDailySummary.date.desc()).limit(30)
    else:
        query = query.order_by(HealthDailySummary.date.desc())
        
    summaries = query.all()
    
    # Map to frontend expected format (camelCase and units)
    mapped_data = []
    for s in summaries:
        mapped_data.append({
            "id": s.id,
            "date": s.date.isoformat(),
            "sleepHours": (s.sleep_duration_minutes or 0) / 60.0,
            "sleepQualityScore": s.sleep_quality_score,
            "stepsCount": s.steps_count or 0,
            "hrvAverage": s.hrv_average,
            "restingHeartRate": s.resting_heart_rate,
            "recoveryScore": int((s.hrv_average or 0) * 2) if s.hrv_average else 50
        })
        
    return {"status": "success", "data": mapped_data}

@router.get("/summary", summary="Get daily health summary")
async def get_health_summary(
    date_str: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from datetime import date
    try:
        summary_date = date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format")
        
    service = HealthService(db)
    summary = service.get_daily_summary(current_user.id, summary_date)
    if not summary:
        return {"message": "No data for this date"}
    return summary

@router.post("/workouts", summary="Log a workout")
async def log_workout(
    workout_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = HealthService(db)
    return service.log_workout(current_user.id, workout_data)

@router.post("/nutrition", summary="Log nutrition")
async def log_nutrition(
    nutrition_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = HealthService(db)
    return service.log_nutrition(current_user.id, nutrition_data)

@router.get("/recovery-score", summary="Get current recovery score")
async def get_recovery_score(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = HealthService(db)
    return {"score": service.calculate_recovery_score(current_user.id)}

@router.post("/sync", summary="Sync mock health data")
async def sync_mock_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = HealthService(db)
    summary = service.sync_mock_data(current_user.id)
    return {"message": "Synced mock data", "summary": summary}

@router.post("/seed", summary="Bulk seed health history")
async def seed_health_history(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Bulk insert health daily summaries for seeding.
    Payload: { "days": [ { "date": "YYYY-MM-DD", "sleep_hours": 7.5, ... } ] }
    """
    days = payload.get("days", [])
    count = 0 
    for d in days:
        try:
            date_obj = datetime.strptime(d["date"], "%Y-%m-%d").date()
            existing = db.query(HealthDailySummary).filter(
                HealthDailySummary.user_id == current_user.id,
                HealthDailySummary.date == date_obj
            ).first()
            
            if not existing:
                existing = HealthDailySummary(
                    id=str(uuid.uuid4()),
                    user_id=current_user.id, 
                    date=date_obj
                )
                db.add(existing)

            # Map fields
            if "sleep_hours" in d: 
                existing.sleep_duration_minutes = int(float(d["sleep_hours"]) * 60)
            if "sleep_quality" in d: existing.sleep_quality_score = d["sleep_quality"]
            if "hrv" in d: existing.hrv_average = d["hrv"]
            if "rhr" in d: existing.resting_heart_rate = d["rhr"]
            if "steps" in d: existing.steps_count = d["steps"]
            if "active_minutes" in d: existing.active_minutes = d["active_minutes"]
            
            count += 1
        except Exception as e:
            continue
            
    db.commit()
    return {"message": f"Seeded {count} days of health data"}
@router.post("/interest", summary="Track feature interest")
async def track_interest(
    payload: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Log user interest in a feature.
    """
    from models.models import FeatureInterest
    
    feature = payload.get("feature")
    if not feature:
        raise HTTPException(status_code=400, detail="Missing feature name")
        
    interest = FeatureInterest(
        user_id=current_user.id,
        feature_name=feature
    )
    db.add(interest)
    db.commit()
    
    return {"message": "Interest recorded"}

@router.get("/users/{user_id}/health/score", summary="Get detailed health score")
async def get_user_health_score(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Auth check
):
    """
    Get 5-pillar Health Score for a specific user.
    """
    if user_id == "me":
        user_id = current_user.id
        
    # Security check: users can only see their own score unless admin (not impl yet)
    if user_id != current_user.id:
        # Check permissions or role if implemented, otherwise strictly forbid
        raise HTTPException(status_code=403, detail="Forbidden: You can only view your own score.")

    from services.health_scoring import compute_health_score
    result = compute_health_score(user_id, db)
    
    return {
        "status": "success",
        "data": {
            "overall": {
                "score": result["health_score"],
                "confidence": result["confidence"],
                "band": result["band"]
            },
            "dimensions": result["dimensions"],
            "recommendations": [] # Future: generate based on lowest pillar
        }
    }

@router.get("/score", summary="Get detailed health score (current user)")
async def get_my_health_score(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get 5-pillar Health Score for current user.
    """
    return await get_user_health_score(current_user.id, db, current_user)
