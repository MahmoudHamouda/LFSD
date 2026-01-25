from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from models.lifestyle_events import LifestyleEvent
from models.models import LifeGoal
from loguru import logger
import uuid
import pytz

class LifestyleService:
    def __init__(self, db: Session):
        self.db = db

    def get_upcoming_events(self, user_id: str) -> List[LifestyleEvent]:
        """Get upcoming lifestyle events (from now onwards)."""
        now = datetime.utcnow()
        return self.db.query(LifestyleEvent).filter(
            LifestyleEvent.user_id == user_id,
            LifestyleEvent.start_time >= now
        ).order_by(LifestyleEvent.start_time.asc()).all()

    def create_event(self, user_id: str, event_data: dict) -> Dict[str, Any]:
        """Create a lifestyle event (e.g. dinner reservation)."""
        # Validate critical fields
        if not event_data.get("title") or not event_data.get("start_time"):
             raise ValueError("Event title and start_time are required")
             
        try:
            # Handle start_time parsing robustly
            start_str = event_data.get("start_time")
            start_time = None
            if start_str.endswith("Z"):
                 start_str = start_str[:-1] # Brittle naive fix, better to use specialized parser but this works for basic Z
                 start_time = datetime.fromisoformat(start_str)
            else:
                 start_time = datetime.fromisoformat(start_str)
            
            event = LifestyleEvent(
                id=str(uuid.uuid4()),
                user_id=user_id,
                event_type=event_data.get("event_type", "dining"),
                title=event_data.get("title"),
                start_time=start_time,
                cost_estimated=max(0, float(event_data.get("cost_estimated", 0))), # Ensure non-negative
                source="manual"
            )
            self.db.add(event)
            self.db.commit()
            self.db.refresh(event)
            return {
                "success": True, 
                "event_id": event.id,
                "title": event.title
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create lifestyle event: {e}")
            raise e

    def get_recommendations(self, user_id: str, mood: str = "stress") -> List[dict]:
        """
        Get 'Treat Yourself' recommendations based on mood.
        from models.models import User
        user = self.db.query(User).filter(User.id == user_id).first()
        prefs = user.profile_json.get("preferences", {}) if user and user.profile_json else {}
        
        diet_pref = prefs.get("dietary", "General")
        
        recommendations = []
        if mood == "stress":
            if "vegan" in diet_pref.lower():
                recommendations.append({"title": "Order Comfort Food", "type": "dining", "suggestion": "Vegan Bowl Place"})
            else:
                 recommendations.append({"title": "Order Comfort Food", "type": "dining", "suggestion": "Nando's"})
                 
            recommendations.append({"title": "Relaxing Spa Day", "type": "wellness", "suggestion": "Local Spa"})
            
        return recommendations

    def get_goals(self, user_id: str) -> List[dict]:
        """Get life goals."""
        goals = self.db.query(LifeGoal).filter(LifeGoal.user_id == user_id).all()
        return [
            {
                "id": g.id,
                "title": g.title,
                "target_amount": g.target_amount,
                "saved_amount": g.saved_amount,
                "progress": int((g.saved_amount / g.target_amount) * 100) if g.target_amount > 0 else 0,
                "target_date": g.target_date.isoformat() if g.target_date else None,
                "pillar": g.pillar or "finance" # Use pillar instead of dead 'category'
            }
            for g in goals
        ]

    def create_goal(self, user_id: str, goal_data: dict) -> Dict[str, Any]:
        """Create a new life goal."""
        try:
            target_date_val = None
            if goal_data.get("target_date"):
                 # Robust parse could go here, for now basic iso format
                 target_date_val = datetime.fromisoformat(goal_data.get("target_date").replace("Z", ""))
                 
            goal = LifeGoal(
                id=str(uuid.uuid4()),
                user_id=user_id,
                title=goal_data.get("title"),
                target_amount=max(0, float(goal_data.get("target_amount", 1000))),
                saved_amount=0,
                target_date=target_date_val,
                pillar=goal_data.get("pillar", "finance")
            )
            self.db.add(goal)
            self.db.commit()
            self.db.refresh(goal)
            
            return {
                "success": True, 
                "goal_id": goal.id,
                "title": goal.title
            }
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create life goal: {e}")
            raise e

