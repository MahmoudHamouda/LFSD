import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from models.models import User, RecurringBill, MobilityTrip, HealthDailySummary, Workout
from services.recommendation_service.recommendation_engine import compute_recommendations
from core.config import get_settings

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def debug_user_recommendations(email):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"❌ User found with email {email} not found.")
            return

        print(f"✅ User found: {user.id} ({user.email})")
        
        # Check Data
        bills = db.query(RecurringBill).filter(RecurringBill.user_id == user.id).all()
        print(f"Recurring Bills: {len(bills)}")
        for b in bills:
            print(f"  - {b.name}: ${b.amount}")

        trips = db.query(MobilityTrip).filter(MobilityTrip.user_id == user.id).all()
        print(f"Mobility Trips: {len(trips)}")
        
        # Run Engine
        recs = compute_recommendations(user.id, db)
        print(f"\nComputed Recommendations: {len(recs)}")
        for r in recs:
            print(f"  - [{r['priority']}] {r['category']}: {r['title']}")
            
        if not recs:
            print("\n⚠️ No recommendations generated. Seeding data to force functionality...")
            seed_data(user.id, db)
            recs_after = compute_recommendations(user.id, db)
            print(f"Computed Recommendations (After Seeding): {len(recs_after)}")
            for r in recs_after:
                print(f"  - [{r['priority']}] {r['category']}: {r['title']}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

def seed_data(user_id, db):
    # Seed 3 Recurring Bills
    db.add_all([
        RecurringBill(user_id=user_id, name="Netflix", amount=15.99, is_verified=True),
        RecurringBill(user_id=user_id, name="Spotify", amount=9.99, is_verified=True),
        RecurringBill(user_id=user_id, name="Adobe Creative Cloud", amount=54.99, is_verified=True)
    ])
    
    # Seed Mobility Trips (3 morning trips)
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    # Go back to a Monday through Wednesday
    base_date = now - timedelta(days=7) 
    
    trips = []
    # Seed 3 trips at 8 AM on consecutive weekdays
    for i in range(3):
        # ensure weekday
        d = base_date + timedelta(days=i)
        while d.weekday() > 4: # Is weekend
            d += timedelta(days=1)
        
        trip_time = d.replace(hour=8, minute=15, second=0)
        trips.append(MobilityTrip(
            user_id=user_id,
            provider="Uber",
            pickup_time=trip_time,
            cost_amount=45.0,
            trip_type="Premium",
            origin_lat=25.2,
            origin_lon=55.2,
            destination_lat=25.3,
            destination_lon=55.3
        ))
    db.add_all(trips)
    
    # Seed Health Data (Low sleep)
    yesterday = datetime.utcnow().date() - timedelta(days=1)
    db.add(HealthDailySummary(
        user_id=user_id,
        date=yesterday,
        sleep_duration_minutes=300, # 5 hours
        steps_count=2000
    ))
    
    db.commit()
    print("✅ Seeded test data (Bills, Commute, Health)")

if __name__ == "__main__":
    debug_user_recommendations("finance@helm.com")
