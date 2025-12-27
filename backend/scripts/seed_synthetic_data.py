import sys
import os
import random
from datetime import datetime, timedelta
import uuid

# Add parent dir to path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database import SessionLocal, engine
from models.models import (
    User, FinancialAccount, Transaction, VivIndex, 
    HealthDailySummary, SleepSession, Workout,
    CalendarEvent, MobilityTrip, LifeGoal, FinancialScore
)
from core.authentication import get_password_hash

# Setup
db = SessionLocal()
PASSWORD_HASH = get_password_hash("P@ssword123")

def generate_uuid():
    return str(uuid.uuid4())

def random_date(start_days_ago=30, end_days_ago=0):
    start = datetime.utcnow() - timedelta(days=start_days_ago)
    end = datetime.utcnow() - timedelta(days=end_days_ago)
    return start + (end - start) * random.random()

def create_user(user_id, email, name, persona_type, bio, preferences):
    """Creates a base user with profile and preferences."""
    existing = db.query(User).filter(User.id == user_id).first()
    if existing:
        print(f"User {name} ({user_id}) already exists. Skipping core creation.")
        return existing
    
    print(f"Creating {name}...")
    user = User(
        id=user_id,
        email=email,
        hashed_password=PASSWORD_HASH,
        profile_json={"name": name, "type": persona_type, "bio": bio},
        viv_preferences=preferences,
        onboarding_status="COMPLETE"
    )
    db.add(user)
    db.commit()
    return user

# ============================================================================
# 1. The Steward (David)
# ============================================================================
def seed_steward():
    user = create_user(
        "user-steward", "steward@helm.com", "David (The Steward)", "Steward",
        "Focused on long-term wealth accumulation and risk mitigation.",
        {"risk_tolerance": "low", "communication_style": "formal"}
    )
    
    # Financials: High Savings, Low Debt
    if not db.query(FinancialAccount).filter_by(user_id=user.id).first():
        acc = FinancialAccount(
            user_id=user.id, institution_name="Vanguard", account_type="investment",
            current_balance=250000.0
        )
        db.add(acc)
        
        # Consistent Income
        db.add(Transaction(
            user_id=user.id, account_id=acc.id, amount=8500.0, 
            description="Salary Deposit", category_primary="Income",
            transaction_date=datetime.utcnow() - timedelta(days=15)
        ))

    # Indices: High Finance, Medium Health, Low Time
    if not db.query(VivIndex).filter_by(user_id=user.id).first():
        db.add(VivIndex(user_id=user.id, financial_score=85.0, health_score=60.0, time_score=45.0))

    db.commit()

    # Financial Score Breakdown
    db.add(FinancialScore(
        user_id=user.id,
        overall_score=85.0,
        cashflow_stability_score=85.0, bills_coverage_score=90.0, savings_rate_score=80.0, debt_load_score=90.0,
        discretionary_control_score=75.0, emergency_buffer_score=85.0, networth_momentum_score=88.0, investment_health_score=90.0,
        time_window="30d", timestamp=datetime.utcnow() 
    ))
    db.commit()

# ============================================================================
# 2. The Operator (Sara)
# ============================================================================
def seed_operator():
    user = create_user(
        "user-operator", "operator@helm.com", "Sara (The Operator)", "Operator",
        "Maximizing human performance and health metrics.",
        {"risk_tolerance": "medium", "communication_style": "direct"}
    )
    
    # Health: High Performance logs
    if not db.query(HealthDailySummary).filter_by(user_id=user.id).first():
        for i in range(7):
            date = datetime.utcnow() - timedelta(days=i)
            db.add(HealthDailySummary(
                user_id=user.id, date=date, 
                sleep_duration_minutes=480 + random.randint(-30, 30),
                sleep_quality_score=90 + random.random() * 10,
                hrv_average=65 + random.random() * 20,
                resting_heart_rate=55
            ))
            
    # Indices: Medium Finance, High Health, Medium Time
    if not db.query(VivIndex).filter_by(user_id=user.id).first():
        db.add(VivIndex(user_id=user.id, financial_score=60.0, health_score=92.0, time_score=65.0))

    db.commit()

# ============================================================================
# 3. The Commander (Alex)
# ============================================================================
def seed_commander():
    user = create_user(
        "user-commander", "commander@helm.com", "Alex (The Commander)", "Commander",
        "Efficiency obsession. Delegates everything possible.",
        {"risk_tolerance": "high", "communication_style": "concise"}
    )
    
    # Time: Busy calendar, lots of mobility
    if not db.query(CalendarEvent).filter_by(user_id=user.id).first():
        for i in range(5):
            start = datetime.utcnow() + timedelta(days=i, hours=9)
            db.add(CalendarEvent(
                user_id=user.id, title="Strategy Sync", 
                start_time=start, end_time=start + timedelta(hours=1),
                is_meeting=True, location_context="office"
            ))
            
    # Indices: High Finance, Low Health, High Time (Efficiency)
    if not db.query(VivIndex).filter_by(user_id=user.id).first():
        db.add(VivIndex(user_id=user.id, financial_score=75.0, health_score=50.0, time_score=88.0))

    db.commit()

# ============================================================================
# 4. Full Data User (Viv Power User)
# ============================================================================
def seed_full_user():
    user = create_user(
        "user-full", "full@helm.com", "Max (Power User)", "Balanced",
        "Has connected every integration and uses the app daily.",
        {"risk_tolerance": "balanced", "communication_style": "friendly"}
    )
    
    # 4.1 Financials
    if not db.query(FinancialAccount).filter_by(user_id=user.id).first():
        checking = FinancialAccount(user_id=user.id, institution_name="Chase", account_type="checking", current_balance=5400.0)
        savings = FinancialAccount(user_id=user.id, institution_name="Ally", account_type="savings", current_balance=32000.0)
        db.add_all([checking, savings])
        db.commit() # Need IDs
        
        # 30 transactions
        categories = ["Food", "Transport", "Shopping", "Bills", "Entertainment"]
        for _ in range(30):
            db.add(Transaction(
                user_id=user.id, account_id=checking.id,
                amount=random.uniform(10, 200),
                description=f"Payment to {random.choice(['Starbucks', 'Uber', 'Amazon', 'ConEd', 'Netflix'])}",
                category_primary=random.choice(categories),
                transaction_date=random_date(30, 0)
            ))
            
    # 4.2 Health
    if not db.query(HealthDailySummary).filter_by(user_id=user.id).first():
        for i in range(30):
            date = datetime.utcnow() - timedelta(days=i)
            db.add(HealthDailySummary(
                user_id=user.id, date=date,
                sleep_duration_minutes=random.randint(400, 500),
                sleep_quality_score=random.uniform(60, 95),
                steps_count=random.randint(5000, 15000)
            ))
            
    # 4.3 Time
    if not db.query(CalendarEvent).filter_by(user_id=user.id).first():
        for i in range(15):
            start = random_date(10, -10) # Past and future
            db.add(CalendarEvent(
                user_id=user.id, title="Deep Work Session",
                start_time=start, end_time=start + timedelta(hours=2),
                is_meeting=False, location_context="wfh"
            ))

    # 4.4 Indices History (Trend)
    if not db.query(VivIndex).filter_by(user_id=user.id).first():
        for i in range(10):
            db.add(VivIndex(
                user_id=user.id,
                timestamp=datetime.utcnow() - timedelta(days=i*3),
                financial_score=70 + i,
                health_score=60 + (i % 3),
                time_score=80 - i
            ))

    db.commit()

    # Financial Score Breakdown
    db.add(FinancialScore(
        user_id=user.id,
        overall_score=78.0,
        cashflow_stability_score=60.0, bills_coverage_score=70.0, savings_rate_score=50.0, debt_load_score=80.0,
        discretionary_control_score=65.0, emergency_buffer_score=70.0, networth_momentum_score=75.0, investment_health_score=80.0,
        time_window="30d", timestamp=datetime.utcnow() 
    ))
    db.commit()

# ============================================================================
# 5. Empty User (Newbie)
# ============================================================================
def seed_empty_user():
    create_user(
        "user-empty", "new@helm.com", "New User", "Undiscovered",
        "Brand new account, no data.",
        {"risk_tolerance": "medium"}
    )
    # No other data added

def main():
    print("Beginning synthetic data seed...")
    try:
        seed_steward()
        seed_operator()
        seed_commander()
        seed_full_user()
        seed_empty_user()
        print("✅ Seeding complete! 5 Users created.")
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
