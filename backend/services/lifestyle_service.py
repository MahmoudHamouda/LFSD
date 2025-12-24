from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from models.lifestyle_events import LifestyleEvent
from models.database import get_db

class LifestyleService:
    def __init__(self, db: Session):
        self.db = db

    def get_upcoming_events(self, user_id: str) -> List[LifestyleEvent]:
        """Get upcoming lifestyle events."""
        now = datetime.utcnow()
        return self.db.query(LifestyleEvent).filter(
            LifestyleEvent.user_id == user_id,
            LifestyleEvent.start_time >= now
        ).order_by(LifestyleEvent.start_time.asc()).all()

    def create_event(self, user_id: str, event_data: dict) -> LifestyleEvent:
        """Create a lifestyle event (e.g. dinner reservation)."""
        event = LifestyleEvent(
            user_id=user_id,
            event_type=event_data.get("event_type", "dining"),
            title=event_data.get("title"),
            start_time=datetime.fromisoformat(event_data.get("start_time")),
            cost_estimated=event_data.get("cost_estimated"),
            source="manual"
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def get_recommendations(self, user_id: str, mood: str = "stress") -> List[dict]:
        """Get 'Treat Yourself' recommendations based on mood."""
        # In a real app, this would query an external API or a recommendation engine
        if mood == "stress":
            return [
                {"title": "Order Comfort Food", "type": "dining", "suggestion": "Nando's"},
                {"title": "Relaxing Spa Day", "type": "wellness", "suggestion": "Local Spa"}
            ]
        return []
    def get_goals(self, user_id: str) -> List[dict]:
        """Get life goals."""
        from models.models import LifeGoal
        goals = self.db.query(LifeGoal).filter(LifeGoal.user_id == user_id).all()
        return [
            {
                "id": g.id,
                "title": g.title,
                "target_amount": g.target_amount,
                "saved_amount": g.saved_amount,
                "progress": int((g.saved_amount / g.target_amount) * 100) if g.target_amount > 0 else 0,
                "deadline": g.deadline.isoformat() if g.deadline else None,
                "category": "personal" # Default for now
            }
            for g in goals
        ]

    def create_goal(self, user_id: str, goal_data: dict) -> bool:
        """Create a new life goal."""
        from models.models import LifeGoal
        goal = LifeGoal(
            user_id=user_id,
            title=goal_data.get("title"),
            target_amount=goal_data.get("target_amount", 1000), # Default target
            saved_amount=0,
            deadline=datetime.fromisoformat(goal_data.get("target_date")) if goal_data.get("target_date") else None
        )
        self.db.add(goal)
        self.db.commit()
        return True
