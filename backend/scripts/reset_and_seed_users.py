import sys
import os
import random
from datetime import datetime, timedelta
import uuid

# Add parent dir to path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database import SessionLocal, engine, Base
from models.models import (
    User, FinancialAccount, Transaction, VivIndex, 
    HealthDailySummary, SleepSession, Workout,
    CalendarEvent, MobilityTrip, LifeGoal, FinancialScore,
    TimeProfile, TimeScore, HealthProfile
)
from core.authentication import get_password_hash
from sqlalchemy import text

# Setup
db = SessionLocal()
PASSWORD_HASH = get_password_hash("P@ssword123")

def random_date(start_days_ago=90, end_days_ago=0):
    start = datetime.utcnow() - timedelta(days=start_days_ago)
    end = datetime.utcnow() - timedelta(days=end_days_ago)
    return start + (end - start) * random.random()

def clean_database():
    print("Cleaning database...")
    try:
        # Drop all tables with CASCADE (Postgres friendly)
        print("Dropping all tables with CASCADE...")
        for table in reversed(Base.metadata.sorted_tables):
            try:
                db.execute(text(f"DROP TABLE IF EXISTS {table.name} CASCADE;"))
            except Exception as e:
                print(f"Warning dropping {table.name}: {e}")
        db.commit()
        
        # Create tables
        print("Creating tables...")
        Base.metadata.create_all(bind=engine)
        
        # Verify deletion
        count = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
        print(f"Force deleted all users via Raw SQL. Remaining count: {count}")

    except Exception as e:
        print(f"[ERROR] Error cleaning database: {e}")
        db.rollback()
        raise e

def create_base_user(user_id, email, name, persona_type, bio):
    print(f"Creating {name} ({email})...")
    user = User(
        id=user_id,
        email=email,
        hashed_password=PASSWORD_HASH,
        profile_json={"name": name, "type": persona_type, "bio": bio},
        viv_preferences={"risk_tolerance": "medium"},
        onboarding_status="COMPLETE"
    )
    db.add(user)
    db.commit()
    return user

def seed_financial_data(user_id):
    print(f"  - Seeding Financial Data for {user_id}...")
    # 1. Accounts
    checking = FinancialAccount(
        user_id=user_id, institution_name="Chase", account_type="checking", 
        current_balance=5000.0 + random.uniform(0, 2000)
    )
    savings = FinancialAccount(
        user_id=user_id, institution_name="Ally", account_type="savings", 
        current_balance=15000.0 + random.uniform(0, 5000)
    )
    db.add_all([checking, savings])
    db.commit()

    # 2. Transactions (Last 3 months)
    categories = ["Food", "Transport", "Shopping", "Bills", "Entertainment", "Groceries", "Rent"]
    for i in range(90): # One per day roughly
        if random.random() > 0.3: # 70% chance of transaction
            db.add(Transaction(
                user_id=user_id, account_id=checking.id,
                amount=random.uniform(10, 150),
                description=f"Purchase at {random.choice(['Target', 'Walmart', 'Uber', 'Shell', 'Whole Foods'])}",
                category_primary=random.choice(categories),
                transaction_date=random_date(1, 0) - timedelta(days=i) # Spread out
            ))
    
    # Income
    for i in range(3):
        db.add(Transaction(
            user_id=user_id, account_id=checking.id,
            amount=4000.0,
            description="Salary",
            category_primary="Income",
            transaction_date=datetime.utcnow() - timedelta(days=30*i + 15)
        ))

    # 3. Life Goals
    db.add(LifeGoal(
        user_id=user_id, title="Emergency Fund", target_amount=20000, 
        saved_amount=15000, priority="high"
    ))

    # 4. Financial Scores (History)
    for i in range(12): # Weekly snapshots
        db.add(FinancialScore(
            user_id=user_id,
            overall_score=70 + i, # Improving
            timestamp=datetime.utcnow() - timedelta(weeks=i)
        ))
    db.commit()

def seed_health_data(user_id):
    print(f"  - Seeding Health Data for {user_id}...")
    # 1. Daily Summaries
    for i in range(90):
        date = datetime.utcnow().date() - timedelta(days=i)
        db.add(HealthDailySummary(
            user_id=user_id, date=date,
            sleep_duration_minutes=random.randint(350, 500),
            sleep_quality_score=random.uniform(60, 90),
            steps_count=random.randint(4000, 12000),
            hrv_average=random.uniform(40, 80),
            resting_heart_rate=random.randint(50, 70)
        ))
    
    # 2. Workouts
    for i in range(30): # Every 3 days
        start = random_date(90, 0)
        db.add(Workout(
            user_id=user_id, 
            start_time=start, end_time=start + timedelta(minutes=45),
            activity_type=random.choice(["Running", "Lifting", "Yoga"]),
            calories_burned=random.randint(200, 600)
        ))
    
    # 3. Health Profile
    db.add(HealthProfile(
        user_id=user_id, diet_style="Balanced", water_intake_range="2-3L",
        activity_self_report="Active"
    ))
    db.commit()

def seed_time_data(user_id):
    print(f"  - Seeding Time Data for {user_id}...")
    # 1. Calendar Events
    for i in range(50):
        start = random_date(90, 0)
        db.add(CalendarEvent(
            user_id=user_id, title=random.choice(["Deep Work", "Meeting", "Sync", "Planning"]),
            start_time=start, end_time=start + timedelta(minutes=60),
            is_meeting=random.choice([True, False]),
            location_context="wfh"
        ))
    
    # 2. Mobility (Uber trips)
    for i in range(15):
        start = random_date(90, 0)
        db.add(MobilityTrip(
            user_id=user_id, provider="Uber",
            pickup_time=start, dropoff_time=start + timedelta(minutes=20),
            cost_amount=random.uniform(15, 40),
            trip_type="economy"
        ))
    
    # 3. Time Profile
    db.add(TimeProfile(
        user_id=user_id, work_hours_per_week="40-50", 
        time_overwhelm_level="Moderate"
    ))

    # 4. Time Scores
    db.commit()

def seed_minimal_finance_profile(user_id):
    # Just a LifeGoal to show they went through onboarding
    db.add(LifeGoal(
        user_id=user_id, title="Save for Rainy Day", target_amount=10000, 
        saved_amount=2000, priority="medium"
    ))
    db.commit()

def seed_minimal_health_profile(user_id):
    db.add(HealthProfile(
        user_id=user_id, diet_style="Average", water_intake_range="1-2L",
        activity_self_report="Lightly Active"
    ))
    db.commit()

def seed_minimal_time_profile(user_id):
    db.add(TimeProfile(
        user_id=user_id, work_hours_per_week="35-40", 
        time_overwhelm_level="Low"
    ))
    db.commit()

def populate_synthetic_data():
    try:
        clean_database()

        # 1. Empty User
        user1 = create_base_user(
            "user-empty", "empty@helm.com", "Empty User", "Newbie", "Just joined."
        )
        user1.onboarding_status = "NOT_STARTED" # Explicitly set
        db.commit()

        # 2. Financial User
        user2 = create_base_user(
            "user-finance", "finance@helm.com", "Finance User", "Planner", "Loves money."
        )
        seed_financial_data(user2.id)
        seed_minimal_health_profile(user2.id)
        seed_minimal_time_profile(user2.id)
        # Add minimal VivIndex for dashboard to load
        db.add(VivIndex(user_id=user2.id, financial_score=85, health_score=55, time_score=55))
        db.commit()

        # 3. Health User
        user3 = create_base_user(
            "user-health", "health@helm.com", "Health User", "Athlete", "Loves health."
        )
        seed_health_data(user3.id)
        seed_minimal_finance_profile(user3.id)
        seed_minimal_time_profile(user3.id)
        db.add(VivIndex(user_id=user3.id, financial_score=55, health_score=88, time_score=55))
        db.commit()

        # 4. Time User
        user4 = create_base_user(
            "user-time", "time@helm.com", "Time User", "Productivity Guru", "Loves efficiency."
        )
        seed_time_data(user4.id)
        seed_minimal_finance_profile(user4.id)
        seed_minimal_health_profile(user4.id)
        db.add(VivIndex(user_id=user4.id, financial_score=55, health_score=55, time_score=82))
        db.commit()

        # 5. Super User
        user5 = create_base_user(
            "user-super", "super@helm.com", "Super User", "Legend", "Has it all."
        )
        seed_financial_data(user5.id)
        seed_health_data(user5.id)
        seed_time_data(user5.id)
        db.add(VivIndex(user_id=user5.id, financial_score=92, health_score=95, time_score=89))
        db.commit()

        print("[OK] Successfully seeded 5 users!")

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[ERROR] Error seeding users: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    populate_synthetic_data()
