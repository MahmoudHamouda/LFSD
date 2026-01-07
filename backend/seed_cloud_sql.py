"""
Seed Cloud SQL database with synthetic data for test users.
Adapted to use the existing test accounts created via signup API.
"""

import sys
import os
import random
from datetime import datetime, timedelta
import uuid

# Use Cloud SQL connection
os.environ["DATABASE_URL"] = "postgresql://lfsd_user:LFSDProd2026SecurePass!@136.119.201.13:5432/lfsd"

# Add parent directories to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.models import (
    User, FinancialAccount, FinancialTransaction, VivIndex,
    HealthDailySummary, SleepSession, Workout,
    CalendarEvent, MobilityTrip, LifeGoal, FinancialScore
)

# Setup
engine = create_engine(os.environ["DATABASE_URL"])
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

def random_date(start_days_ago=30, end_days_ago=0):
    start = datetime.utcnow() - timedelta(days=start_days_ago)
    end = datetime.utcnow() - timedelta(days=end_days_ago)
    return start + (end - start) * random.random()

def get_user_by_email(email):
    """Get existing user by email."""
    return db.query(User).filter(User.email == email).first()

def seed_finance_user():
    """Seed comprehensive financial data for finance@helm.com"""
    user = get_user_by_email("finance@helm.com")
    if not user:
        print("❌ finance@helm.com user not found!")
        return
    
    print(f"\n📊 Seeding financial data for {user.email}...")
    
    # Update onboarding status
    user.onboarding_status = "COMPLETED"
    user.profile_json = user.profile_json or {}
    user.profile_json.update({"type": "Steward", "bio": "Focused on long-term wealth accumulation"})
    
    # Financial Accounts
    if not db.query(FinancialAccount).filter_by(user_id=user.id).first():
        checking = FinancialAccount(
            user_id=user.id, institution_name="Chase", 
            account_type="checking", current_balance=8500.0
        )
        savings = FinancialAccount(
            user_id=user.id, institution_name="Vanguard",
            account_type="savings", current_balance=45000.0
        )
        investment = FinancialAccount(
            user_id=user.id, institution_name="Fidelity",
            account_type="investment", current_balance=125000.0
        )
        db.add_all([checking, savings, investment])
        db.commit()
        
        # Generate transactions (30 days)
        categories = ["Income", "Food", "Transport", "Bills", "Shopping", "Entertainment"]
        for i in range(40):
            if i % 10 == 0:  # Monthly income
                db.add(FinancialTransaction(
                    user_id=user.id, account_id=checking.id,
                    amount=7500.0, description="Salary Deposit",
                    category_primary="Income",
                    transaction_date=random_date(30, 0)
                ))
            else:  # Expenses
                db.add(FinancialTransaction(
                    user_id=user.id, account_id=checking.id,
                    amount=-random.uniform(15, 350),
                    description=f"Payment to {random.choice(['Whole Foods', 'Uber', 'Amazon', 'Utilities', 'Target'])}",
                    category_primary=random.choice(categories[1:]),
                    transaction_date=random_date(30, 0)
                ))
    
    # VivIndex scores
    if not db.query(VivIndex).filter_by(user_id=user.id).first():
        db.add(VivIndex(
            user_id=user.id, 
            financial_score=85.0, 
            health_score=65.0, 
            time_score=55.0
        ))
    
    # Financial Score Breakdown
    db.add(FinancialScore(
        user_id=user.id, overall_score=85.0,
        cashflow_stability_score=85.0, bills_coverage_score=90.0,
        savings_rate_score=80.0, debt_load_score=95.0,
        discretionary_control_score=75.0, emergency_buffer_score=85.0,
        networth_momentum_score=88.0, investment_health_score=90.0,
        time_window="30d", timestamp=datetime.utcnow()
    ))
    
    # Life Goals
    if not db.query(LifeGoal).filter_by(user_id=user.id).first():
        db.add(LifeGoal(
            user_id=user.id,
            title="Retirement Fund",
            type="retirement",
            target_amount=2000000.0,
            saved_amount=125000.0,
            target_date=datetime.utcnow() + timedelta(days=7300)  # 20 years
        ))
    
    db.commit()
    print("✓ Finance user seeded")

def seed_health_user():
    """Seed comprehensive health data for health@helm.com"""
    user = get_user_by_email("health@helm.com")
    if not user:
        print("❌ health@helm.com user not found!")
        return
    
    print(f"\n💪 Seeding health data for {user.email}...")
    
    user.onboarding_status = "COMPLETED"
    user.profile_json = user.profile_json or {}
    user.profile_json.update({"type": "Operator", "bio": "Maximizing human performance"})
    
    # Health Daily Summaries
    if not db.query(HealthDailySummary).filter_by(user_id=user.id).first():
        for i in range(30):
            date = datetime.utcnow() - timedelta(days=i)
            db.add(HealthDailySummary(
                user_id=user.id, date=date,
                sleep_duration_minutes=random.randint(420, 510),
                sleep_quality_score=random.uniform(75, 98),
                hrv_average=random.uniform(50, 80),
                resting_heart_rate=random.randint(52, 65),
                steps_count=random.randint(8000, 15000)
            ))
    
    # Workouts
    if not db.query(Workout).filter_by(user_id=user.id).first():
        workout_types = ["Running", "Weightlifting", "Yoga", "Cycling", "Swimming"]
        for i in range(15):
            db.add(Workout(
                user_id=user.id,
                workout_type=random.choice(workout_types),
                duration_minutes=random.randint(30, 90),
                calories_burned=random.randint(200, 600),
                start_time=random_date(30, 0)
            ))
    
    # VivIndex
    if not db.query(VivIndex).filter_by(user_id=user.id).first():
        db.add(VivIndex(
            user_id=user.id,
            financial_score=60.0,
            health_score=92.0,
            time_score=65.0
        ))
    
    db.commit()
    print("✓ Health user seeded")

def seed_time_user():
    """Seed comprehensive time/productivity data for time@helm.com"""
    user = get_user_by_email("time@helm.com")
    if not user:
        print("❌ time@helm.com user not found!")
        return
    
    print(f"\n⏰ Seeding time data for {user.email}...")
    
    user.onboarding_status = "COMPLETED"
    user.profile_json = user.profile_json or {}
    user.profile_json.update({"type": "Commander", "bio": "Efficiency obsessed"})
    
    # Calendar Events
    if not db.query(CalendarEvent).filter_by(user_id=user.id).first():
        event_types = ["Meeting", "Deep Work", "Review", "Planning", "Break"]
        for i in range(25):
            start = random_date(10, -10)  # Past and future
            db.add(CalendarEvent(
                user_id=user.id,
                title=f"{random.choice(event_types)} Session",
                start_time=start,
                end_time=start + timedelta(hours=random.randint(1, 3)),
                is_meeting=random.choice([True, False]),
                location_context=random.choice(["office", "wfh", "coworking"])
            ))
    
    # Mobility Trips
    if not db.query(MobilityTrip).filter_by(user_id=user.id).first():
        for i in range(10):
            db.add(MobilityTrip(
                user_id=user.id,
                mode=random.choice(["car", "uber", "metro", "walk"]),
                distance_km=random.uniform(2, 25),
                cost_aed=random.uniform(10, 150),
                trip_date=random_date(20, 0)
            ))
    
    # VivIndex
    if not db.query(VivIndex).filter_by(user_id=user.id).first():
        db.add(VivIndex(
            user_id=user.id,
            financial_score=72.0,
            health_score=55.0,
            time_score=88.0
        ))
    
    db.commit()
    print("✓ Time user seeded")

def seed_super_user():
    """Seed comprehensive data across all pillars for super@helm.com"""
    user = get_user_by_email("super@helm.com")
    if not user:
        print("❌ super@helm.com user not found!")
        return
    
    print(f"\n🌟 Seeding comprehensive data for {user.email}...")
    
    user.onboarding_status = "COMPLETED"
    user.profile_json = user.profile_json or {}
    user.profile_json.update({"type": "Power User", "bio": "Full integration user"})
    
    # Add financial data
    if not db.query(FinancialAccount).filter_by(user_id=user.id).first():
        checking = FinancialAccount(
            user_id=user.id, institution_name="Chase",
            account_type="checking", current_balance=5400.0
        )
        db.add(checking)
        db.commit()
        
        for _ in range(20):
            db.add(Transaction(
                user_id=user.id, account_id=checking.id,
                amount=-random.uniform(10, 200),
                description=f"Payment",
                category_primary=random.choice(["Food", "Transport", "Shopping"]),
                transaction_date=random_date(30, 0)
            ))
    
    # Add health data
    if not db.query(HealthDailySummary).filter_by(user_id=user.id).first():
        for i in range(14):
            db.add(HealthDailySummary(
                user_id=user.id, date=datetime.utcnow() - timedelta(days=i),
                sleep_duration_minutes=random.randint(400, 500),
                steps_count=random.randint(6000, 12000)
            ))
    
    # Add time data
    if not db.query(CalendarEvent).filter_by(user_id=user.id).first():
        for i in range(10):
            start = random_date(5, -5)
            db.add(CalendarEvent(
                user_id=user.id, title="Meeting",
                start_time=start, end_time=start + timedelta(hours=1),
                is_meeting=True
            ))
    
    # VivIndex with history
    if not db.query(VivIndex).filter_by(user_id=user.id).first():
        for i in range(10):
            db.add(VivIndex(
                user_id=user.id,
                timestamp=datetime.utcnow() - timedelta(days=i*3),
                financial_score=70 + random.randint(-5, 10),
                health_score=65 + random.randint(-5, 10),
                time_score=75 + random.randint(-5, 10)
            ))
    
    db.commit()
    print("✓ Super user seeded")

def seed_empty_user():
    """Update empty user status"""
    user = get_user_by_email("empty@helm.com")
    if not user:
        print("❌ empty@helm.com user not found!")
        return
    
    print(f"\n📭 Configuring empty user {user.email}...")
    user.onboarding_status = "COMPLETED"
    user.profile_json = user.profile_json or {}
    user.profile_json.update({"type": "New User", "bio": "Just getting started"})
    db.commit()
    print("✓ Empty user configured (no data added)")

def main():
    print("=" * 80)
    print("🌱 SEEDING CLOUD SQL DATABASE")
    print("=" * 80)
    
    try:
        seed_finance_user()
        seed_health_user()
        seed_time_user()
        seed_super_user()
        seed_empty_user()
        
        print("\n" + "=" * 80)
        print("✅ SEEDING COMPLETE!")
        print("=" * 80)
        print("\nUsers seeded:")
        print("  - finance@helm.com (Financial focus)")
        print("  - health@helm.com (Health focus)")
        print("  - time@helm.com (Time/productivity focus)")
        print("  - super@helm.com (Power user - all data)")
        print("  - empty@helm.com (New user - minimal data)")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
