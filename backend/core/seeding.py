import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models.models import (
    FinancialAccount, FinancialTransaction,
    HealthDailySummary, SleepSession, VivIndex, CalendarEvent,
    LifeGoal
)

def seed_user_data(db: Session, user_id: str, profile: str = "finance"):
    """
    Seeds initial data for a user if they have none.
    """
    print(f"Checking data for user {user_id}...")
    
    # Check if data exists (checking Financial Account as proxy)
    if db.query(FinancialAccount).filter(FinancialAccount.user_id == user_id).first():
        print(f"User {user_id} already has data. Skipping seed.")
        return False

    print(f"Seeding data for {user_id}...")
    try:
        if profile == "finance":
            _add_financial_data(db, user_id)
            _add_life_goals(db, user_id)
            _add_viv_index(db, user_id)
            _add_health_data(db, user_id)
            _add_time_data(db, user_id)
        
        # Add other profiles if needed later
        
        return True
    except Exception as e:
        print(f"Error seeding data: {e}")
        return False

def _add_financial_data(db: Session, user_id: str):
    checking = FinancialAccount(
        id=str(uuid.uuid4()), user_id=user_id, institution_name="Chase Bank",
        account_type="checking", current_balance=5250.00
    )
    savings = FinancialAccount(
        id=str(uuid.uuid4()), user_id=user_id, institution_name="Chase Bank",
        account_type="savings", current_balance=12500.00
    )
    db.add(checking)
    db.add(savings)
    
    # Transactions
    today = datetime.utcnow()
    transactions = [
        {"days": 1, "amt": -45.20, "merch": "Whole Foods", "cat": "groceries"},
        {"days": 2, "amt": -12.50, "merch": "Starbucks", "cat": "dining"},
        {"days": 3, "amt": 3200.00, "merch": "Salary Deposit", "cat": "income"},
        {"days": 5, "amt": -85.00, "merch": "Shell", "cat": "transportation"},
        {"days": 7, "amt": -1250.00, "merch": "Apartment Rent", "cat": "housing"},
        {"days": 10, "amt": -67.89, "merch": "Amazon", "cat": "shopping"},
        {"days": 14, "amt": -120.00, "merch": "Equinox", "cat": "health"},
    ]
    for txn in transactions:
        t = FinancialTransaction(
            id=str(uuid.uuid4()), account_id=checking.id, user_id=user_id,
            amount=txn["amt"], merchant_name=txn["merch"], category_primary=txn["cat"],
            transaction_date=today - timedelta(days=txn["days"])
        )
        db.add(t)

def _add_life_goals(db: Session, user_id: str):
    goals = [
        {"title": "Emergency Fund", "pillar": "financial", "target": 10000.0, "saved": 2500.0, "prio": "high"},
        {"title": "Marathon Training", "pillar": "health", "target": 0.0, "saved": 0.0, "prio": "medium"},
    ]
    for g in goals:
        goal = LifeGoal(
            id=str(uuid.uuid4()), user_id=user_id, title=g["title"], pillar=g["pillar"],
            target_amount=g["target"], saved_amount=g["saved"], priority=g["prio"],
            target_date=datetime.utcnow() + timedelta(days=180)
        )
        db.add(goal)

def _add_viv_index(db: Session, user_id: str):
    viv = VivIndex(
        id=str(uuid.uuid4()), user_id=user_id,
        financial_score=78.0, health_score=65.0, time_score=50.0,
        snapshot_reason="Seeding", timestamp=datetime.utcnow()
    )
    db.add(viv)

def _add_health_data(db: Session, user_id: str):
    today = datetime.utcnow().date()
    for d in range(5):
        h = HealthDailySummary(
            id=str(uuid.uuid4()), user_id=user_id, date=today - timedelta(days=d),
            steps_count=8500 + (d*100), hrv_average=45.0, resting_heart_rate=60
        )
        db.add(h)

def _add_time_data(db: Session, user_id: str):
    today = datetime.utcnow()
    events = [
        {"title": "Deep Work", "hours": 2, "dur": 120},
        {"title": "Team Sync", "hours": 5, "dur": 30},
    ]
    for e in events:
        ev = CalendarEvent(
            id=str(uuid.uuid4()), user_id=user_id, title=e["title"],
            start_time=today + timedelta(hours=e["hours"]),
            end_time=today + timedelta(hours=e["hours"], minutes=e["dur"])
        )
        db.add(ev)
