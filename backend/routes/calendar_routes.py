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

    conn = (
        db.query(Connection)
        .filter(Connection.user_id == user_id, Connection.provider == "google_calendar")
        .first()
    )

    if conn and conn.status == "connected":
        return {"status": "connected"}
    return {"status": "disconnected"}


from datetime import datetime
from models.models import CalendarEvent
from core.authentication import get_current_user
from models.models import User
import uuid


class EventCreate(BaseModel):
    title: str
    start_time: str
    end_time: str
    is_meeting: bool = False


@router.post("/events")
async def create_event(
    event: EventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Manual event creation for seeding."""
    e = CalendarEvent(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        title=event.title,
        start_time=datetime.fromisoformat(event.start_time.replace("Z", "+00:00")),
        end_time=datetime.fromisoformat(event.end_time.replace("Z", "+00:00")),
        is_meeting=event.is_meeting,
        source="manual_seeding",
    )
    db.add(e)
    db.commit()
    return {"status": "success", "id": e.id}
