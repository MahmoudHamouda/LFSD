import sys
import os
import uuid
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.models import User, HealthDailySummary

# Using direct connection string matching checking scripts
DATABASE_URL = "postgresql+psycopg2://postgres:LfsdSecure2024!@136.119.201.13:5432/lfsd"

def seed_health_summary():
    # Database setup
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Find user
        user = db.query(User).filter(User.email == "health@helm.com").first()
        if not user:
            print("User health@helm.com not found!")
            return

        print(f"Seeding health summary for user: {user.email}")
        
        today = date.today()
        
        # Check if exists
        summary = db.query(HealthDailySummary).filter(
            HealthDailySummary.user_id == user.id,
            HealthDailySummary.date == today
        ).first()
        
        if summary:
            print("Summary already exists, updating...")
            summary.sleep_duration_minutes = 450 # 7.5h
            summary.sleep_quality_score = 75
            summary.steps_count = 8500
            summary.hrv_average = 45
            summary.resting_heart_rate = 60
        else:
            print("Creating new summary...")
            summary = HealthDailySummary(
                id=str(uuid.uuid4()),
                user_id=user.id,
                date=today,
                sleep_duration_minutes=450, # 7.5h
                sleep_quality_score=75,
                steps_count=8500,
                hrv_average=45,
                resting_heart_rate=60
            )
            db.add(summary)
            
        db.commit()
        print("✅ Health summary seeded successfully.")
        
    except Exception as e:
        print(f"Error seeding health: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_health_summary()
