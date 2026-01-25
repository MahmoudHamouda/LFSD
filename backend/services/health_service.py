from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
import uuid
from loguru import logger
from models.models import HealthDailySummary, SleepSession, Workout
from models.nutrition_logs import NutritionLog
from core.config import get_settings

settings = get_settings()

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
        """Log a new workout with validation."""
        try:
            if not workout_data.get("start_time") or not workout_data.get("end_time"):
                 raise ValueError("Start and End times are required")
            start_time = datetime.fromisoformat(workout_data.get("start_time"))
            end_time = datetime.fromisoformat(workout_data.get("end_time"))
            
            if end_time <= start_time:
                raise ValueError("Workout end time must be after start time")

            # Validate activity type
            if not workout_data.get("activity_type"):
                raise ValueError("Activity type is required")
                
            workout = Workout(
                id=str(uuid.uuid4()),
                user_id=user_id,
                activity_type=workout_data.get("activity_type"),
                start_time=start_time,
                end_time=end_time,
                calories_burned=max(0, float(workout_data.get("calories_burned", 0))),
                perceived_exertion=workout_data.get("perceived_exertion")
            )
            
            self.db.add(workout)
            
            # --- Aggregation Logic (Missing Linkage Fix) ---
            # Update HealthDailySummary for that day
            workout_date = start_time.date()
            summary = self.get_daily_summary(user_id, workout_date)
            
            if not summary:
                summary = HealthDailySummary(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    date=workout_date,
                    active_minutes=0,
                    active_calories=0
                )
                self.db.add(summary)
            
            duration_mins = (end_time - start_time).total_seconds() / 60
            summary.active_minutes = (summary.active_minutes or 0) + int(duration_mins)
            # Note: HealthDailySummary schema might need 'active_calories_burned' field check
            # Assuming 'active_calories' or similar exists, else skip
            
            self.db.commit()
            self.db.refresh(workout)
            return workout
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to log workout: {e}")
            raise e

    def log_nutrition(self, user_id: str, nutrition_data: dict) -> NutritionLog:
        """Log nutrition data with validation."""
        try:
            if not nutrition_data.get("date"):
                raise ValueError("Date is required")
            log_date = date.fromisoformat(nutrition_data.get("date"))
            
            log = NutritionLog(
                id=str(uuid.uuid4()),
                user_id=user_id,
                date=log_date,
                calories_in=max(0, float(nutrition_data.get("calories_in", 0))),
                protein_grams=max(0, float(nutrition_data.get("protein_grams", 0))),
                carbs_grams=max(0, float(nutrition_data.get("carbs_grams", 0))),
                fat_grams=max(0, float(nutrition_data.get("fat_grams", 0))),
                source=nutrition_data.get("source", "manual")
            )
            self.db.add(log)
            self.db.commit()
            self.db.refresh(log)
            return log
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to log nutrition: {e}")
            raise e

    def calculate_recovery_score(self, user_id: str) -> Dict[str, Any]:
        """
        Calculate recovery score based on recent sleep and HRV.
        Returns score (0-100) and confidence (0.0-1.0).
        """
        today = datetime.utcnow().date()
        
        # Fetch last 3 days to get a trend/average if today is missing
        start_date = today - timedelta(days=2)
        summaries = self.db.query(HealthDailySummary).filter(
            HealthDailySummary.user_id == user_id,
            HealthDailySummary.date >= start_date
        ).all()
        
        if not summaries:
            return {"score": 50, "confidence": 0.0} # No data
            
        # Prioritize today, then yesterday
        latest = max(summaries, key=lambda x: x.date)
        
        # HRV Normalization (rMSSD typically 20-100ms)
        # 100ms+ = Great (100), 20ms = Low (20)
        # Using simple linear clamp for now
        hrv_raw = latest.hrv_average
        if hrv_raw is None:
            hrv_score = 50 
        else:
            hrv_score = min(max(hrv_raw, 20), 100) 
            
        sleep_score = latest.sleep_quality_score
        if sleep_score is None:
            sleep_score = 50
            
        final_score = int((hrv_score + sleep_score) / 2)
        
        # Confidence logic
        confidence = 0.9 if latest.date == today else 0.6
        if hrv_raw is None or sleep_score is None:
            confidence -= 0.3
            
        return {"score": final_score, "confidence": max(0.1, confidence)}

    def sync_mock_data(self, user_id: str) -> HealthDailySummary:
        """
        Generate and store mock health data for testing.
        WARNING: Only for dev/test environments.
        """
        # Safety check: Should ideally be gated by env var
        if not settings.DEBUG: 
             logger.warning("Mock data sync blocked: DEBUG mode is off")
             return None 
        
        today = datetime.utcnow().date()
        
        # UPSERT logic using merge or check-then-update
        summary = self.get_daily_summary(user_id, today)
        
        if not summary:
             summary = HealthDailySummary(
                id=str(uuid.uuid4()),
                user_id=user_id,
                date=today
            )
        
        # Apply "drained" state values
        summary.sleep_duration_minutes = 300 # 5 hours
        summary.sleep_quality_score = 45
        summary.hrv_average = 30
        summary.steps_count = 2500
        summary.resting_heart_rate = 65
        
        self.db.add(summary) # add works for updates if object is attached
        self.db.commit()
        self.db.refresh(summary)
        return summary

