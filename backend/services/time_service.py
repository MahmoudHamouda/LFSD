from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
from models.models import CalendarEvent, User
from models.database import get_db

class TimeService:
    def __init__(self, db: Session):
        self.db = db

    def get_upcoming_events(self, user_id: str, limit: int = 10) -> List[CalendarEvent]:
        """Get upcoming calendar events."""
        now = datetime.utcnow()
        return self.db.query(CalendarEvent).filter(
            CalendarEvent.user_id == user_id,
            CalendarEvent.start_time >= now
        ).order_by(CalendarEvent.start_time.asc()).limit(limit).all()

    def create_event(self, user_id: str, event_data: dict) -> CalendarEvent:
        """Create a new calendar event."""
        event = CalendarEvent(
            user_id=user_id,
            title=event_data.get("title"),
            start_time=datetime.fromisoformat(event_data.get("start_time")),
            end_time=datetime.fromisoformat(event_data.get("end_time")),
            is_meeting=event_data.get("is_meeting", False),
            location_context=event_data.get("location_context", "wfh")
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def calculate_busy_score(self, user_id: str, date: datetime) -> int:
        """Calculate busy score (0-100) for a given day."""
        start_of_day = date.replace(hour=0, minute=0, second=0)
        end_of_day = date.replace(hour=23, minute=59, second=59)
        
        events = self.db.query(CalendarEvent).filter(
            CalendarEvent.user_id == user_id,
            CalendarEvent.start_time >= start_of_day,
            CalendarEvent.start_time <= end_of_day
        ).all()
        
        total_minutes = 0
        for event in events:
            duration = (event.end_time - event.start_time).total_seconds() / 60
            total_minutes += duration
            
        # Simple heuristic: 8 hours (480 mins) = 100% busy
        score = min(int((total_minutes / 480) * 100), 100)
        return score
