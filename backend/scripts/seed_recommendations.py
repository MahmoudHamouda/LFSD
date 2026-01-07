import sys
import os
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.models import User, RecurringBill, MobilityTrip, HealthDailySummary

# Hardcoded DB URL for dev environment (Consistent with config.py default)
DATABASE_URL = "sqlite:///lfsd_v2.db"

def seed_data():
    print("Connecting to database...")
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
      # Find User - target steward@helm.com for demo
        user = session.query(User).filter(User.email == "steward@helm.com").first()
        if not user:
            print("User 'steward@helm.com' not found. Creating...")
            import uuid
            from core.authentication import get_password_hash
            new_user = User(
                id=str(uuid.uuid4()),
                email="steward@helm.com",
                hashed_password=get_password_hash("password123")
            )
            session.add(new_user)
            session.commit()
            user = new_user
            print(f"Created user: {user.email}")

        user_id = user.id
        print(f"Found user: {user.email} ({user_id})")

        # 1. Trigger Finance Recommendation (Optimize Subscriptions)
        # Need >= 3 recurring bills
        # Check existing bills
        bills_count = session.query(RecurringBill).filter_by(user_id=user_id).count()
        if bills_count < 3:
            print(f"Adding {3 - bills_count} recurring bills...")
            for i in range(3 - bills_count):
                bill = RecurringBill(
                    user_id=user_id,
                    name=f"Subscription {i+1}",
                    amount=15.0 + (i * 5),
                    cadence="monthly",
                    category="Subscription",
                    next_due_date=datetime.datetime.utcnow().date()
                )
                session.add(bill)
        
        # 2. Trigger Time Recommendation (Automate Commute)
        # Need >= 3 morning trips (7-9 AM) in last 30 days
        print("Checking/Adding morning trips...")
        # Add 3 trips in the last week at 8 AM
        for i in range(3):
            trip_date = datetime.datetime.utcnow() - datetime.timedelta(days=i+1)
            # Ensure weekday
            while trip_date.weekday() >= 5:
                trip_date -= datetime.timedelta(days=1)
            
            trip_time = trip_date.replace(hour=8, minute=0, second=0)
            
            # Check if trip exists roughly then
            exists = session.query(MobilityTrip).filter(
                MobilityTrip.user_id == user_id,
                MobilityTrip.pickup_time == trip_time
            ).first()
            
            if not exists:
                trip = MobilityTrip(
                    user_id=user_id,
                    provider="Uber",
                    pickup_time=trip_time,
                    dropoff_time=trip_time + datetime.timedelta(minutes=30),
                    cost_amount=25.0,
                    currency="USD",
                    trip_type="economy"
                )
                session.add(trip)
                print(f"Added trip on {trip_time}")

        # 3. Trigger Health Recommendation (Schedule Recovery)
        # Need Low Sleep (< 6h) yesterday OR High Exertion today
        print("Forcing Low Sleep for yesterday...")
        yesterday = datetime.datetime.utcnow().date() - datetime.timedelta(days=1)
        
        # Check summary for yesterday
        summary = session.query(HealthDailySummary).filter(
            HealthDailySummary.user_id == user_id,
            HealthDailySummary.date == yesterday
        ).first()
        
        if summary:
            summary.sleep_duration_minutes = 300 # 5 hours
            summary.steps_count = 12500
            print("Updated existing summary to 5h sleep and 12.5k steps.")
        else:
            summary = HealthDailySummary(
                user_id=user_id,
                date=yesterday,
                sleep_duration_minutes=300, # 5 hours (Triggers Recommendation)
                sleep_score=50,
                steps_count=12500 # > 8000 (Triggers Treat)
            )
            session.add(summary)
            print("Created new summary with 5h sleep and 12.5k steps.")

        session.commit()
        print("✅ Data seeded successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    seed_data()
