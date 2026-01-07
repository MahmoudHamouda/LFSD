import uuid
from datetime import datetime, timedelta
from models.database import SessionLocal
from models.models import (
    User, LifeGoal, FinancialAccount, FinancialTransaction,
    HealthDailySummary, SleepSession, VivIndex, CalendarEvent
)

def seed_finance_user():
    db = SessionLocal()
    try:
        # 1. Fetch user
        user = db.query(User).filter(User.email == "finance@helm.com").first()
        if not user:
            print("❌ User finance@helm.com NOT FOUND.")
            return
        
        print(f"✅ Found user: {user.id}")
        user_id = user.id

        # 2. Add Financial Data
        print("Seeding Financial Data...")
        _add_financial_data(db, user_id)

        # 3. Add Health Data
        print("Seeding Health Data...")
        _add_health_data(db, user_id)

        # 4. Add Life Goals
        print("Seeding Life Goals...")
        _add_life_goals(db, user_id)

        # 5. Add Viv Index
        print("Seeding Viv Index...")
        _add_viv_index(db, user_id)
        
        # 6. Add Calendar Events
        print("Seeding Calendar Data...")
        _add_time_data(db, user_id)

        print("🎉 Seeding Complete!")

    except Exception as e:
        print(f"Error seeding user: {e}")
        db.rollback()
    finally:
        db.close()

def _add_financial_data(db, user_id):
    # Check if account exists
    if db.query(FinancialAccount).filter(FinancialAccount.user_id == user_id).first():
        print("  Financial data already exists.")
        return

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
    db.commit()

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
    db.commit()

def _add_life_goals(db, user_id):
    if db.query(LifeGoal).filter(LifeGoal.user_id == user_id).first():
        print("  Goals already exist.")
        return

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
    db.commit()

def _add_viv_index(db, user_id):
    viv = VivIndex(
        id=str(uuid.uuid4()), user_id=user_id,
        financial_score=78.0, health_score=65.0, time_score=50.0,
        snapshot_reason="Seeding", timestamp=datetime.utcnow()
    )
    db.add(viv)
    db.commit()

def _add_health_data(db, user_id):
    today = datetime.utcnow().date()
    for d in range(5):
        h = HealthDailySummary(
            id=str(uuid.uuid4()), user_id=user_id, date=today - timedelta(days=d),
            steps_count=8500 + (d*100), hrv_average=45.0, resting_heart_rate=60
        )
        db.add(h)
    db.commit()

def _add_time_data(db, user_id):
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
    db.commit()

if __name__ == "__main__":
    seed_finance_user()
