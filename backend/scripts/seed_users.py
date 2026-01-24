"""
Comprehensive user seeding script for LFSD application.
Creates all test users with complete onboarding status and sample data.
"""

from datetime import datetime, timedelta
from models.database import engine, SessionLocal, Base
from models.models import (
    User, LifeGoal, FinancialAccount, FinancialTransaction,
    HealthDailySummary, SleepSession, Workout, VivIndex,
    CalendarEvent, MobilityTrip, VivLog, Order,
    FinancialScore, TimeScore
)
from core.authentication import get_password_hash
import uuid

def safe_seed_users():
    """Seed users without dropping tables (Safe for production)."""
    db = SessionLocal()
    try:
        users_to_create = [
            {
                "id": "user-finance",
                "email": "finance@helm.com",
                "password": "P@ssword123",
                "name": "Finance User",
                "profile": "finance"
            },
            {
                "id": "user-empty",
                "email": "empty@helm.com",
                "password": "P@ssword123",
                "name": "Empty User",
                "profile": "empty"
            },
            {
                "id": "user-health",
                "email": "health@helm.com",
                "password": "P@ssword123",
                "name": "Health User",
                "profile": "health"
            },
            {
                "id": "user-time",
                "email": "time@helm.com",
                "password": "P@ssword123",
                "name": "Time User",
                "profile": "time"
            },
            {
                "id": "user-super",
                "email": "super@helm.com",
                "password": "P@ssword123",
                "name": "Super User",
                "profile": "super"
            },
            # Standard Personas (Mapped to profiles for data generation)
            {
                "id": "user-david",
                "email": "david@example.com",
                "password": "password",
                "name": "David",
                "profile": "finance"
            },
            {
                "id": "user-sara",
                "email": "sara@example.com",
                "password": "password",
                "name": "Sara",
                "profile": "health"
            },
            {
                "id": "user-alex",
                "email": "alex@example.com",
                "password": "password",
                "name": "Alex",
                "profile": "time"
            }
        ]
        
        for user_data in users_to_create:
            # Check existing first
            existing = db.query(User).filter(User.email == user_data["email"]).first()
            if existing:
                print(f"User {user_data['email']} exists. Updating onboarding status and password...")
                existing.onboarding_status = "COMPLETE"
                existing.hashed_password = get_password_hash(user_data["password"])
                db.commit()
                # Ensure we have the user object
                user = existing
            else:
                print(f"Creating user {user_data['email']}...")
                user = User(
                    id=user_data["id"],
                    email=user_data["email"],
                    hashed_password=get_password_hash(user_data["password"]),
                    profile_json={"name": user_data["name"]},
                    onboarding_status="COMPLETE"
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                print(f"User {user_data['email']} created.")
            
            # Add sample data based on profile
            profile = user_data["profile"]
            
            if profile in ["finance", "super"]:
                _add_financial_data(db, user.id)
            
            if profile in ["health", "super"]:
                _add_health_data(db, user.id)
            
            if profile in ["time", "super", "finance"]:
                _add_time_data(db, user.id)
            
            if profile == "super":
                _add_life_goals(db, user.id)
            
            _add_viv_index(db, user.id, profile)
        
        print("Safe seeding completed successfully!")
        
    except Exception as e:
        print(f"Error seeding users: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        # Raise it so we see the full stack in terminal
        raise e
    finally:
        db.close()

def seed_all_users():
    """Seed all test users with strict schema reset (Use with caution)."""
    print("Resetting database schema...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    safe_seed_users()


def _add_financial_data(db, user_id):
    """Add sample financial accounts and transactions."""
    # Check if account already exists
    existing_account = db.query(FinancialAccount).filter(
        FinancialAccount.user_id == user_id
    ).first()
    
    if existing_account:
        print(f"  Financial data already exists for {user_id}")
        return
    
    # Create checking account
    checking = FinancialAccount(
        id=str(uuid.uuid4()),
        user_id=user_id,
        institution_name="Chase Bank",
        account_type="checking",
        current_balance=5250.00
    )
    db.add(checking)
    
    # Create savings account
    savings = FinancialAccount(
        id=str(uuid.uuid4()),
        user_id=user_id,
        institution_name="Chase Bank",
        account_type="savings",
        current_balance=12500.00
    )
    db.add(savings)
    db.commit()
    db.refresh(checking)
    
    # Add transactions for the last 30 days
    today = datetime.utcnow()
    transactions = [
        {"days_ago": 1, "amount": -45.20, "merchant": "Whole Foods", "category": "groceries"},
        {"days_ago": 2, "amount": -12.50, "merchant": "Starbucks", "category": "dining"},
        {"days_ago": 3, "amount": 3200.00, "merchant": "Salary Deposit", "category": "income"},
        {"days_ago": 5, "amount": -85.00, "merchant": "Gas Station", "category": "transportation"},
        {"days_ago": 7, "amount": -1250.00, "merchant": "Rent Payment", "category": "housing"},
        {"days_ago": 10, "amount": -67.89, "merchant": "Amazon", "category": "shopping"},
        {"days_ago": 14, "amount": -120.00, "merchant": "Gym Membership", "category": "health"},
        {"days_ago": 20, "amount": -89.99, "merchant": "Electric Bill", "category": "utilities"},
    ]
    
    for txn_data in transactions:
        txn = FinancialTransaction(
            id=str(uuid.uuid4()),
            account_id=checking.id,
            user_id=user_id,
            amount=txn_data["amount"],
            merchant_name=txn_data["merchant"],
            category_primary=txn_data["category"],
            transaction_date=today - timedelta(days=txn_data["days_ago"])
        )
        db.add(txn)
    
    db.commit()
    print(f"  Added financial data for {user_id}")


def _add_health_data(db, user_id):
    """Add sample health metrics."""
    existing = db.query(HealthDailySummary).filter(
        HealthDailySummary.user_id == user_id
    ).first()
    
    if existing:
        print(f"  Health data already exists for {user_id}")
        return
    
    today = datetime.utcnow().date()
    
    # Add last 7 days of health summaries
    for days_ago in range(7):
        date = today - timedelta(days=days_ago)
        summary = HealthDailySummary(
            id=str(uuid.uuid4()),
            user_id=user_id,
            date=date,
            steps_count=8000 + (days_ago * 500),
            hrv_average=45.0 + days_ago,
            resting_heart_rate=62 - days_ago
        )
        db.add(summary)
    
    # Add sleep sessions
    for days_ago in range(7):
        start_time = datetime.utcnow() - timedelta(days=days_ago, hours=8)
        sleep = SleepSession(
            id=str(uuid.uuid4()),
            user_id=user_id,
            start_time=start_time,
            end_time=start_time + timedelta(hours=7, minutes=30),
            deep_sleep_minutes=90 + days_ago * 5,
            rem_sleep_minutes=120 - days_ago * 3,
            wake_count=2
        )
        db.add(sleep)
    
    db.commit()
    print(f"  Added health data for {user_id}")


def _add_time_data(db, user_id):
    """Add sample calendar events."""
    existing = db.query(CalendarEvent).filter(
        CalendarEvent.user_id == user_id
    ).first()
    
    if existing:
        print(f"  Calendar data already exists for {user_id}")
        return
    
    today = datetime.utcnow()
    
    # Add upcoming meetings
    events = [
        {"hours": 2, "title": "Team Standup", "duration": 30},
        {"hours": 5, "title": "Client Call", "duration": 60},
        {"hours": 24, "title": "Project Review", "duration": 90},
    ]
    
    for event_data in events:
        event = CalendarEvent(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=event_data["title"],
            start_time=today + timedelta(hours=event_data["hours"]),
            end_time=today + timedelta(hours=event_data["hours"], minutes=event_data["duration"])
            # calendar_id removed
        )
        db.add(event)
    
    db.commit()
    print(f"  Added calendar data for {user_id}")


def _add_life_goals(db, user_id):
    """Add sample life goals."""
    existing = db.query(LifeGoal).filter(
        LifeGoal.user_id == user_id
    ).first()
    
    if existing:
        print(f"  Goals already exist for {user_id}")
        return
    
    goals = [
        {
            "title": "Emergency Fund",
            "category": "financial",
            "target_amount": 10000.00,
            "saved_amount": 2500.00,
            "priority": "high"
        },
        {
            "title": "Get Fit",
            "category": "health",
            "target_amount": 0.0,
            "saved_amount": 0.0,
            "priority": "medium"
        }
    ]
    
    for goal_data in goals:
        goal = LifeGoal(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=goal_data["title"],
            pillar=goal_data["category"], # Map category from seed data to pillar in model
            target_amount=goal_data["target_amount"],
            saved_amount=goal_data["saved_amount"],
            target_date=datetime.utcnow() + timedelta(days=365), # Renamed from deadline
            priority=goal_data["priority"]
        )
        db.add(goal)
    
    db.commit()
    print(f"  Added life goals for {user_id}")


def _add_viv_index(db, user_id, profile):
    """Add VivIndex snapshot."""
    existing = db.query(VivIndex).filter(
        VivIndex.user_id == user_id
    ).first()
    
    if existing:
        print(f"  VivIndex already exists for {user_id}")
        return
    
    # Calculate scores based on profile
    if profile == "finance":
        financial, health, time = 75.0, 50.0, 50.0
    elif profile == "health":
        financial, health, time = 50.0, 80.0, 50.0
    elif profile == "time":
        financial, health, time = 50.0, 50.0, 85.0
    elif profile == "super":
        financial, health, time = 80.0, 85.0, 82.0
    else:  # empty
        financial, health, time = 45.0, 40.0, 38.0
    
    viv_index = VivIndex(
        id=str(uuid.uuid4()),
        user_id=user_id,
        financial_score=financial,
        health_score=health,
        time_score=time,
        snapshot_reason="Initial Seeding",
        timestamp=datetime.utcnow()
    )
    db.add(viv_index)
    db.commit()
    print(f"  Added VivIndex for {user_id}")


if __name__ == "__main__":
    print("Starting comprehensive user seeding...")
    seed_all_users()
    print("Seeding complete!")
