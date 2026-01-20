import sys
import os
import random
from datetime import datetime, timedelta
import uuid

# Add parent dir to path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database import SessionLocal, engine, Base
from models.models import (
    User, FinancialAccount, FinancialTransaction, VivIndex, 
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

# ============================================================================
# RICH DATA SEEDING (90 Days + Goals + Trends)
# ============================================================================

def seed_rich_finance_data(user_id):
    print(f"  - Seeding RICH Financial Data for {user_id}...")
    
    # 1. Accounts
    checking = FinancialAccount(
        user_id=user_id, institution_name="Chase", account_type="checking", 
        current_balance=12500.00
    )
    savings = FinancialAccount(
        user_id=user_id, institution_name="Ally", account_type="savings", 
        current_balance=45000.00
    )
    credit_card = FinancialAccount(
        user_id=user_id, institution_name="Amex", account_type="credit", 
        current_balance=-1200.00, limit=15000.0
    )
    db.add_all([checking, savings, credit_card])
    db.commit() # Get IDs

    # 2. Transactions (Last 90 days)
    # Pattern: Salary 15th/30th. Rent 1st. Groceries Weekly. Coffee Daily.
    
    categories = ["Food", "Transport", "Shopping", "Entertainment", "Groceries", "Utilities"]
    start_date = datetime.utcnow() - timedelta(days=90)
    
    for day in range(90):
        current_date = start_date + timedelta(days=day)
        
        # Income (Salary) - Bi-monthly
        if current_date.day in [15, 30]:
             db.add(FinancialTransaction(
                user_id=user_id, account_id=checking.id,
                amount=5000.0,
                description="TechCorp Salary",
                category_primary="Income",
                transaction_date=current_date
            ))
        
        # Expenses (Rent) - Monthly
        if current_date.day == 1:
            db.add(FinancialTransaction(
                user_id=user_id, account_id=checking.id,
                amount=-2500.0,
                description="Luxury Apartments Rent",
                category_primary="Rent",
                transaction_date=current_date
            ))

        # Daily Spend
        if random.random() > 0.1: # 90% chance of spend
            db.add(FinancialTransaction(
                user_id=user_id, account_id=credit_card.id,
                amount=-random.uniform(5, 15),
                description="Starbucks Coffee",
                category_primary="Food",
                transaction_date=current_date
            ))
        
        # Weekly Spend
        if current_date.weekday() == 5: # Saturday Grocery Run
            db.add(FinancialTransaction(
                user_id=user_id, account_id=credit_card.id,
                amount=-random.uniform(150, 300),
                description="Whole Foods",
                category_primary="Groceries",
                transaction_date=current_date
            ))

    # 3. Life Goals (Structured for Trends)
    # Goal 1: House Downpayment - In Progress
    db.add(LifeGoal(
        user_id=user_id, title="House Downpayment", target_amount=100000, 
        saved_amount=45000, priority="high", pillar="finance",
        type="house", monthly_contribution_target=2000.0
    ))
    # Goal 2: Emergency Fund - Completed
    db.add(LifeGoal(
        user_id=user_id, title="Emergency Fund", target_amount=20000, 
        saved_amount=20000, priority="medium", pillar="finance",
        type="emergency_fund"
    ))
    
    # 4. Financial Scores (History for Graph)
    # Trend: Slowly improving
    for i in range(12): # 12 Weeks
        db.add(FinancialScore(
            user_id=user_id,
            overall_score=75 + (i * 0.5), # 75 -> 81
            timestamp=datetime.utcnow() - timedelta(weeks=12-i)
        ))
    db.commit()


def seed_rich_health_data(user_id):
    print(f"  - Seeding RICH Health Data for {user_id}...")
    
    # 1. Daily Summaries (90 Days)
    # Trend: Good sleep, high activity
    start_date = datetime.utcnow() - timedelta(days=90)
    for day in range(90):
        current_date = start_date + timedelta(days=day)
        
        is_weekend = current_date.weekday() >= 5
        steps = random.randint(8000, 15000) if not is_weekend else random.randint(12000, 20000)
        
        db.add(HealthDailySummary(
            user_id=user_id, date=current_date.date(),
            sleep_duration_minutes=random.randint(420, 540), # 7-9 hours
            sleep_quality_score=random.uniform(75, 95),
            steps_count=steps,
            hrv_average=random.uniform(55, 90),
            resting_heart_rate=random.randint(45, 60)
        ))

    # 2. Workouts (Consistent)
    for i in range(40): # ~3 times a week
        start = random_date(90, 0)
        db.add(Workout(
            user_id=user_id, 
            start_time=start, end_time=start + timedelta(minutes=60),
            activity_type=random.choice(["CrossFit", "Running", "Cycling"]),
            calories_burned=random.randint(400, 800)
        ))

    # 3. Health Goals
    db.add(LifeGoal(
        user_id=user_id, title="Boston Marathon Qualify", target_amount=100, 
        saved_amount=75, priority="high", pillar="health",
        type="fitness", impact_vector_json={"health": 100}
    ))
    
    # 4. Profile
    db.add(HealthProfile(
        user_id=user_id, diet_style="Paleo", water_intake_range="3L+",
        activity_self_report="Athlete", stress_level="Low"
    ))
    db.commit()

def seed_rich_time_data(user_id):
    print(f"  - Seeding RICH Time Data for {user_id}...")
    
    # 1. Calendar Events (Rich work weeks)
    start_date = datetime.utcnow() - timedelta(days=90)
    for day in range(90):
        current_date = start_date + timedelta(days=day)
        
        if current_date.weekday() < 5: # Weekdays
            # Standup
            db.add(CalendarEvent(
                user_id=user_id, title="Daily Standup",
                start_time=current_date.replace(hour=9, minute=0),
                end_time=current_date.replace(hour=9, minute=30),
                is_meeting=True, location_context="office"
            ))
            # Focus Block
            db.add(CalendarEvent(
                user_id=user_id, title="Deep Work Block",
                start_time=current_date.replace(hour=10, minute=0),
                end_time=current_date.replace(hour=12, minute=0),
                is_meeting=False, location_context="office"
            ))
            # Some random meetings
            if random.random() > 0.5:
                db.add(CalendarEvent(
                    user_id=user_id, title="Project Sync",
                    start_time=current_date.replace(hour=14, minute=0),
                    end_time=current_date.replace(hour=15, minute=0),
                    is_meeting=True, location_context="office"
                ))

    # 2. Time Goals
    db.add(LifeGoal(
        user_id=user_id, title="Limit Meetings to 10h/week", target_amount=10, 
        saved_amount=12, priority="medium", pillar="time", # currently failing
        type="productivity"
    ))

    # 3. Profile
    db.add(TimeProfile(
        user_id=user_id, work_hours_per_week="45", 
        time_overwhelm_level="Low", task_style="Time Blocking"
    ))
    
    # 4. Scores
    for i in range(12):
        db.add(TimeScore(
            user_id=user_id, overall_score=80 + random.uniform(-2, 2),
            timestamp=datetime.utcnow() - timedelta(weeks=12-i)
        ))
    db.commit()

# ============================================================================
# MINIMAL DATA SEEDING (14 Days - Just enough for calc)
# ============================================================================

def seed_minimal_finance_data(user_id):
    print(f"  - Seeding MINIMAL Finance Data for {user_id}...")
    # 1 Account
    checking = FinancialAccount(
        user_id=user_id, institution_name="SimpleBank", account_type="checking", 
        current_balance=2000.0
    )
    db.add(checking)
    db.commit()
    
    # 14 days of coffee
    for i in range(14):
         db.add(FinancialTransaction(
                user_id=user_id, account_id=checking.id,
                amount=-5.0, description="Coffee", category_primary="Food",
                transaction_date=datetime.utcnow() - timedelta(days=i)
        ))
    
    # Viv Score Data
    db.add(FinancialScore(user_id=user_id, overall_score=50, timestamp=datetime.utcnow()))
    db.commit()

def seed_minimal_health_data(user_id):
    print(f"  - Seeding MINIMAL Health Data for {user_id}...")
    # 14 Days summaries
    for i in range(14):
         db.add(HealthDailySummary(
            user_id=user_id, date=datetime.utcnow().date() - timedelta(days=i),
            steps_count=5000, sleep_duration_minutes=400
        ))
    db.add(HealthProfile(user_id=user_id, diet_style="None"))
    db.commit()

def seed_minimal_time_data(user_id):
    print(f"  - Seeding MINIMAL Time Data for {user_id}...")
    # Just a few events
    for i in range(5):
        start = datetime.utcnow() - timedelta(days=i)
        db.add(CalendarEvent(
            user_id=user_id, title="Work",
            start_time=start, end_time=start + timedelta(hours=8),
            is_meeting=False
        ))
    db.add(TimeProfile(user_id=user_id, work_hours_per_week="40"))
    db.commit()


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def populate_synthetic_data():
    try:
        clean_database()

        # 1. Empty User (No data at all)
        print("--- User 1: Empty ---")
        user1 = create_base_user(
            "user-empty", "empty@helm.com", "Empty User", "Newbie", "Just joined."
        )
        user1.onboarding_status = "NOT_STARTED"
        db.commit()

        # 2. Finance User (Rich Finance, Min others)
        print("--- User 2: Finance ---")
        user2 = create_base_user(
            "user-finance", "finance@helm.com", "Finance User", "Planner", "Loves money."
        )
        seed_rich_finance_data(user2.id)
        seed_minimal_health_data(user2.id)
        seed_minimal_time_data(user2.id)
        db.add(VivIndex(user_id=user2.id, financial_score=85, health_score=50, time_score=50))
        db.commit()

        # 3. Health User (Rich Health, Min others)
        print("--- User 3: Health ---")
        user3 = create_base_user(
            "user-health", "health@helm.com", "Health User", "Athlete", "Loves health."
        )
        seed_rich_health_data(user3.id)
        seed_minimal_finance_data(user3.id)
        seed_minimal_time_data(user3.id)
        db.add(VivIndex(user_id=user3.id, financial_score=50, health_score=88, time_score=50))
        db.commit()

        # 4. Time User (Rich Time, Min others)
        print("--- User 4: Time ---")
        user4 = create_base_user(
            "user-time", "time@helm.com", "Time User", "Productivity Guru", "Loves efficiency."
        )
        seed_rich_time_data(user4.id)
        seed_minimal_finance_data(user4.id)
        seed_minimal_health_data(user4.id)
        db.add(VivIndex(user_id=user4.id, financial_score=50, health_score=50, time_score=82))
        db.commit()

        # 5. Super User (Rich EVERYTHING)
        print("--- User 5: Super ---")
        user5 = create_base_user(
            "user-super", "super@helm.com", "Super User", "Legend", "Has it all."
        )
        seed_rich_finance_data(user5.id)
        seed_rich_health_data(user5.id)
        seed_rich_time_data(user5.id)
        db.add(VivIndex(user_id=user5.id, financial_score=92, health_score=95, time_score=89))
        db.commit()

        print("\n[OK] Successfully seeded all 5 personas!")

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[ERROR] Error seeding users: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    populate_synthetic_data()
