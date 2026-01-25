from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models.database import get_db
from services.productivity.google_calendar_service import GoogleCalendarService
import logging

router = APIRouter(prefix="/api/calendar", tags=["calendar"])
logger = logging.getLogger(__name__)

from pydantic import BaseModel

class CodePayload(BaseModel):
    code: str

@router.get("/google/auth-url")
async def get_google_auth_url(db: Session = Depends(get_db)):
    """Generate OAuth2 URL for Calendar verification."""
    # Instantiating with mock user since we might not have one yet in onboarding
    service = GoogleCalendarService(db, user_id="pending_user")
    return {"url": service.get_auth_url()}

@router.post("/google/callback")
async def google_auth_callback(payload: CodePayload, db: Session = Depends(get_db)):
    """Handle OAuth2 callback for Calendar."""
    # We might need to store this partially until user is fully created, 
    # OR if this step is after signup, we attach to user.
    # For now, we perform the exchange to verify it works and return success.
    # In a real app we'd attach to the current session/user.
    service = GoogleCalendarService(db, user_id="pending_user")
    try:
        creds = service.exchange_code(payload.code)
        # Verify connectivity by listing calendars or just succeed
        # service.list_events() 
        return {"status": "success", "message": "Calendar connected"}
    except Exception as e:
        logger.error(f"Calendar Auth Error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/status")
async def get_status(db: Session = Depends(get_db)):
    """
    Checks connection status.
    """
    # We need user_id to check status. For now, assuming "default_user" or we need auth.
    # The original code didn't use user_id, which suggests it was a single-user local app or broken.
    # I'll use "default_user" as a placeholder to match other parts of the system if no auth is present.
    user_id = "default_user" 
    
    # Check DB for connection
    from models.models import Connection
    conn = db.query(Connection).filter(
        Connection.user_id == user_id,
        Connection.provider == "google_calendar"
    ).first()
    
    if conn and conn.status == "connected":
        return {"status": "connected"}
    return {"status": "disconnected"}
