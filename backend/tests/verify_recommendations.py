import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from services.recommendation_service.recommendation_engine import compute_recommendations
from models.models import RecurringBill, MobilityTrip, Workout, HealthDailySummary
from models.database import SessionLocal, Base, engine

# Override database to use local SQLite for testing
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Use a local test DB to avoid Postgres connection issues
TEST_DATABASE_URL = "sqlite:///./test_recs.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables if not exist (for test)
Base.metadata.create_all(bind=engine)

def test_recommendations():
    db = None
    try:
        db = SessionLocal()
        user_id = "test_user_rec_1"
        
        print("Cleaning up old test data...")
        # Cleanup
        db.query(RecurringBill).filter(RecurringBill.user_id == user_id).delete()
        db.query(MobilityTrip).filter(MobilityTrip.user_id == user_id).delete()
        db.commit()
        
        print("Seeding test data...")
        # Seed 3 recurring bills
        b1 = RecurringBill(user_id=user_id, name="Netflix", amount=15.0)
        b2 = RecurringBill(user_id=user_id, name="Hulu", amount=12.0)
        b3 = RecurringBill(user_id=user_id, name="Gym", amount=50.0)
        db.add_all([b1, b2, b3])
        
        # Seed Mobility Trips (3 morning trips)
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        # Ensure weekday
        while now.weekday() > 4:
            now -= timedelta(days=1)
        
        # 8 AM today
        t1_time = now.replace(hour=8, minute=0, second=0, microsecond=0)
        # 8 AM yesterday
        t2_time = t1_time - timedelta(days=1)
        if t2_time.weekday() > 4: t2_time -= timedelta(days=2)
        # 8 AM day before
        t3_time = t2_time - timedelta(days=1)
        if t3_time.weekday() > 4: t3_time -= timedelta(days=2)

        t1 = MobilityTrip(user_id=user_id, provider="Uber", pickup_time=t1_time)
        t2 = MobilityTrip(user_id=user_id, provider="Uber", pickup_time=t2_time)
        t3 = MobilityTrip(user_id=user_id, provider="Uber", pickup_time=t3_time)
        db.add_all([t1, t2, t3])
        
        db.commit()
        
        print("Running recommendation engine...")
        recs = compute_recommendations(user_id, db)
        
        print(f"Recommendations found: {len(recs)}")
        for r in recs:
            print(f"- [{r['priority']}] {r['title']}")
            
        # Assertions
        sub_rec = next((r for r in recs if r['category'] == 'FINANCIAL'), None)
        time_rec = next((r for r in recs if r['category'] == 'TIME'), None)
        
        if sub_rec:
            print("✅ Financial Rec Found")
        else:
            print("❌ Financial Rec Missing")
            
        if time_rec:
            print("✅ Time Rec Found")
        else:
            print("❌ Time Rec Missing")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if db:
            db.close()

if __name__ == "__main__":
    test_recommendations()
