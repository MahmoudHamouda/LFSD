from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import List, Optional
import uuid
from models.models import HealthDailySummary, SleepSession, Workout
from models.nutrition_logs import NutritionLog
from models.database import get_db

class HealthService:
    def __init__(self, db: Session):
        self.db = db

    def get_daily_summary(self, user_id: str, summary_date: date) -> Optional[HealthDailySummary]:
        """Get health summary for a specific date."""
        return self.db.query(HealthDailySummary).filter(
            HealthDailySummary.user_id == user_id,
            HealthDailySummary.date == summary_date
        ).first()

    def log_workout(self, user_id: str, workout_data: dict) -> Workout:
        """Log a new workout."""
        workout = Workout(
            user_id=user_id,
            activity_type=workout_data.get("activity_type"),
            start_time=datetime.fromisoformat(workout_data.get("start_time")),
            end_time=datetime.fromisoformat(workout_data.get("end_time")),
            calories_burned=workout_data.get("calories_burned"),
            perceived_exertion=workout_data.get("perceived_exertion")
        )
        self.db.add(workout)
        self.db.commit()
        self.db.refresh(workout)
        return workout

    def log_nutrition(self, user_id: str, nutrition_data: dict) -> NutritionLog:
        """Log nutrition data."""
        log = NutritionLog(
            user_id=user_id,
            date=date.fromisoformat(nutrition_data.get("date")),
            calories_in=nutrition_data.get("calories_in"),
            protein_grams=nutrition_data.get("protein_grams"),
            carbs_grams=nutrition_data.get("carbs_grams"),
            fat_grams=nutrition_data.get("fat_grams"),
            source=nutrition_data.get("source", "manual")
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def calculate_recovery_score(self, user_id: str) -> int:
        """Calculate recovery score based on recent sleep and HRV."""
        # This would be more complex in production
        today = date.today()
        summary = self.get_daily_summary(user_id, today)
        if not summary:
            return 50 # Default
            
        hrv_score = min((summary.hrv_average or 0) / 100 * 100, 100)
        sleep_score = (summary.sleep_quality_score or 0)
        
        return int((hrv_score + sleep_score) / 2)

    def sync_mock_data(self, user_id: str) -> HealthDailySummary:
        """
        Generate and store mock health data for testing.
        Creates a 'drained' state: Low sleep, low HRV.
        """
        today = date.today()
        
        # Check if exists
        existing = self.get_daily_summary(user_id, today)
        if existing:
            # Update existing to be 'drained'
            existing.sleep_duration_minutes = 300 # 5 hours
            existing.sleep_quality_score = 45
            existing.hrv_average = 30
            existing.steps_count = 2500
            # existing.active_calories = 150 # Not in model
            self.db.commit()
            self.db.refresh(existing)
            return existing
            
        # Create new
        summary = HealthDailySummary(
            id=str(uuid.uuid4()),
            user_id=user_id,
            date=today,
            sleep_duration_minutes=300, # 5 hours
            sleep_quality_score=45,
            hrv_average=30,
            steps_count=2500,
            resting_heart_rate=65
        )
        self.db.add(summary)
        self.db.commit()
        self.db.refresh(summary)
        return summary
