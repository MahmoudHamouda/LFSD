"""
Safe User Seeder (Prod/Dev agnostic, controlled by Caller)
"""

import sys
import os
import random
from datetime import datetime, timedelta, timezone
import uuid
import logging

from models.database import SessionLocal, engine, Base
from models.models import (
    User, FinancialAccount, FinancialTransaction, VivIndex, 
    HealthDailySummary, SleepSession, Workout,
    CalendarEvent, MobilityTrip, LifeGoal, FinancialScore,
    TimeProfile, TimeScore, HealthProfile
)
from core.config import get_settings
from sqlalchemy import text

# Dummy function to avoid ImportError if auth module changed
def get_password_hash(password: str) -> str:
    return "seeded_hash_" + password
from sqlalchemy import text

logger = logging.getLogger(__name__)

# ============================================================================
# UTILS
# ============================================================================

db = SessionLocal()
PASSWORD_HASH = get_password_hash("P@ssword123")

def random_date(start_days_ago=90, end_days_ago=0):
    start = datetime.now(timezone.utc) - timedelta(days=start_days_ago)
    end = datetime.now(timezone.utc) - timedelta(days=end_days_ago)
    return start + (end - start) * random.random()

# ============================================================================
# USER CREATION
# ============================================================================

def create_base_user(user_id, email, name, persona_type, bio, auth0_id=None):
    """
    Create or update a user. If user already exists (by email OR auth0_id),
    returns the existing user instead of creating a new one with the provided user_id.
    """
    print(f"   Creating/Updating {name} ({email})...")
    
    # Check if exists by email OR auth0_id
    existing = db.query(User).filter(
        (User.email == email) | (User.auth0_id == auth0_id)
    ).first() if auth0_id else db.query(User).filter(User.email == email).first()
    
    if existing:
        print(f"   User {email} already exists with ID {existing.id}. Will seed data for this ID.")
        # Ensure Auth0 ID is set if provided
        if auth0_id and existing.auth0_id != auth0_id:
             print(f"   UPDATING Auth0 ID for {email}...")
             existing.auth0_id = auth0_id
             db.commit()
        # Update profile to ensure consistency
        existing.profile_json = {"name": name, "type": persona_type, "bio": bio}
        existing.onboarding_status = "COMPLETE"
        db.commit()
        return existing

    # Create new user ONLY if doesn't exist
    user = User(
        id=user_id,
        email=email,
        hashed_password=PASSWORD_HASH,
        profile_json={"name": name, "type": persona_type, "bio": bio},
        viv_preferences={"risk_tolerance": "medium"},
        onboarding_status="COMPLETE",
        auth0_id=auth0_id
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"   Created new user with ID {user.id}")
    return user

# ============================================================================
# DATA SEEDING
# ============================================================================

def seed_rich_finance_data(user_id):
    print(f"      💰 Seeding rich financial data...")
    try:
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
        db.commit()

        start_date = datetime.now(timezone.utc) - timedelta(days=90)
        for day in range(90):
            current_date = start_date + timedelta(days=day)
            if current_date.day in [15, 30]:
                db.add(FinancialTransaction(user_id=user_id, account_id=checking.id, amount=5000.0, description="TechCorp Salary", category_primary="Income", transaction_date=current_date))
            if current_date.day == 1:
                db.add(FinancialTransaction(user_id=user_id, account_id=checking.id, amount=-2500.0, description="Rent Payment", category_primary="Rent", transaction_date=current_date))
            if random.random() > 0.1:
                db.add(FinancialTransaction(user_id=user_id, account_id=credit_card.id, amount=-random.uniform(5, 15), description="Starbucks", category_primary="Food", transaction_date=current_date))
            if current_date.weekday() == 5:
                db.add(FinancialTransaction(user_id=user_id, account_id=credit_card.id, amount=-random.uniform(150, 300), description="Whole Foods", category_primary="Groceries", transaction_date=current_date))

        db.add(LifeGoal(user_id=user_id, title="House Downpayment", target_amount=100000, saved_amount=45000, priority="high", pillar="finance", type="house", monthly_contribution_target=2000.0))
        db.add(LifeGoal(user_id=user_id, title="Emergency Fund", target_amount=20000, saved_amount=20000, priority="medium", pillar="finance", type="emergency_fund"))
        
        for i in range(12):
            db.add(FinancialScore(user_id=user_id, overall_score=75 + (i * 0.5), timestamp=datetime.now(timezone.utc) - timedelta(weeks=12-i)))
        db.commit()
    except Exception as e:
        print(f"Error seeding finance: {e}")
        db.rollback()

def seed_rich_health_data(user_id):
    print(f"      💪 Seeding rich health data...")
    try:
        start_date = datetime.now(timezone.utc) - timedelta(days=90)
        for day in range(90):
            current_date = start_date + timedelta(days=day)
            is_weekend = current_date.weekday() >= 5
            steps = random.randint(8000, 15000) if not is_weekend else random.randint(12000, 20000)
            db.add(HealthDailySummary(user_id=user_id, date=current_date.date(), sleep_duration_minutes=random.randint(420, 540), sleep_quality_score=random.uniform(75, 95), steps_count=steps, hrv_average=random.uniform(55, 90), resting_heart_rate=random.randint(45, 60)))
        
        for i in range(40):
            start = random_date(90, 0)
            db.add(Workout(user_id=user_id, start_time=start, end_time=start + timedelta(minutes=60), activity_type=random.choice(["CrossFit", "Running", "Cycling"]), calories_burned=random.randint(400, 800)))

        db.add(LifeGoal(user_id=user_id, title="Boston Marathon Qualify", target_amount=100, saved_amount=75, priority="high", pillar="health", type="fitness", impact_vector_json={"health": 100}))
        db.add(HealthProfile(user_id=user_id, diet_style="Paleo", water_intake_range="3L+", activity_self_report="Athlete", stress_level="Low"))
        db.commit()
    except Exception as e:
        print(f"Error seeding health: {e}")
        db.rollback()


def seed_rich_time_data(user_id):
    print(f"      📅 Seeding rich time data...")
    try:
        start_date = datetime.now(timezone.utc) - timedelta(days=90)
        for day in range(90):
            current_date = start_date + timedelta(days=day)
            if current_date.weekday() < 5:
                db.add(CalendarEvent(user_id=user_id, title="Daily Standup", start_time=current_date.replace(hour=9, minute=0), end_time=current_date.replace(hour=9, minute=30), is_meeting=True, location_context="office"))
                db.add(CalendarEvent(user_id=user_id, title="Deep Work Block", start_time=current_date.replace(hour=10, minute=0), end_time=current_date.replace(hour=12, minute=0), is_meeting=False, location_context="office"))
                if random.random() > 0.5:
                    db.add(CalendarEvent(user_id=user_id, title="Project Sync", start_time=current_date.replace(hour=14, minute=0), end_time=current_date.replace(hour=15, minute=0), is_meeting=True, location_context="office"))

        db.add(LifeGoal(user_id=user_id, title="Limit Meetings to 10h/week", target_amount=10, saved_amount=12, priority="medium", pillar="time", type="productivity"))
        db.add(TimeProfile(user_id=user_id, work_hours_per_week="45", time_overwhelm_level="Low", task_style="Time Blocking"))
        for i in range(12):
            db.add(TimeScore(user_id=user_id, overall_score=80 + random.uniform(-2, 2), timestamp=datetime.now(timezone.utc) - timedelta(weeks=12-i)))
        db.commit()
    except Exception as e:
        print(f"Error seeding time: {e}")
        db.rollback()

def seed_minimal_finance_data(user_id):
    checking = FinancialAccount(user_id=user_id, institution_name="SimpleBank", account_type="checking", current_balance=2000.0)
    db.add(checking)
    db.commit()
    for i in range(14):
        db.add(FinancialTransaction(user_id=user_id, account_id=checking.id, amount=-5.0, description="Coffee", category_primary="Food", transaction_date=datetime.now(timezone.utc) - timedelta(days=i)))
    db.add(FinancialScore(user_id=user_id, overall_score=50, timestamp=datetime.now(timezone.utc)))
    db.commit()

def seed_minimal_health_data(user_id):
    for i in range(14):
        db.add(HealthDailySummary(user_id=user_id, date=(datetime.now(timezone.utc) - timedelta(days=i)).date(), steps_count=5000, sleep_duration_minutes=400))
    db.add(HealthProfile(user_id=user_id, diet_style="None"))
    db.commit()

def seed_minimal_time_data(user_id):
    for i in range(5):
        start = datetime.now(timezone.utc) - timedelta(days=i)
        db.add(CalendarEvent(user_id=user_id, title="Work", start_time=start, end_time=start + timedelta(hours=8), is_meeting=False))
    db.add(TimeProfile(user_id=user_id, work_hours_per_week="40"))
    db.commit()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def safe_seed_users():
    """Main seeding function - creates 5 test personas"""
    settings = get_settings()
    print(f"🚀 SEEDING USERS in {settings.ENV}...")
    
    # NOTE: We do NOT clean/drop DB here because safe_seed_users is called AFTER init_db
    # If we want to guarantee clean slate, we should rely on init_db being called before this.
    # However, create_base_user handles existing users gracefully.
    
    try:
        # 1. Empty User
        print("1️⃣  Empty User")
        user1 = create_base_user("user-empty", "empty@helm.com", "Empty User", "Newbie", "Just joined.")
        
        # 2. Finance User
        print("2️⃣  Finance User")
        # HARDCODED AUTH0 ID FOR DEMO STABILITY
        AUTH0_ID_FINANCE = "auth0|69597173abf4ff34ae629c16" 
        user2 = create_base_user("user-finance", "finance@helm.com", "Finance User", "Planner", "Wealth focus.", auth0_id=AUTH0_ID_FINANCE)
        seed_rich_finance_data(user2.id)
        seed_minimal_health_data(user2.id)
        seed_minimal_time_data(user2.id)
        
        # Calculate scores dynamically from seeded data
        print("   Calculating scores from seeded data...")
        from services.financial_scoring import calculate_financial_health_score
        from services.health_scoring import calculate_health_score
        from services.time_service import calculate_time_score
        
        # Create realistic onboarding data for Finance User
        finance_onboarding = {
            "monthly_income": 7500,
            "monthly_bills": 1800,  # Rent, utilities, insurance
            "discretionary_spend": 1200,  # Dining, entertainment, shopping
            "monthly_savings": 1500,  # 20% savings rate
            "cash_balance": 15000,  # Emergency fund
            "investments_value": 45000,  # 401k + brokerage
            "monthly_debt_payments": 300  # Car loan
        }
        
        # Financial score with realistic data
        fin_result = calculate_financial_health_score(user2.id, finance_onboarding, db, is_manual_mode=False)
        financial_score = fin_result.get("overall_score", 50)
        
        # Health score - needs onboarding data structure
        health_result = calculate_health_score(user2.id, {}, db)
        health_score = health_result.get("score", 50) if isinstance(health_result, dict) else 50
        
        # Time score - returns TimeScore object
        time_result = calculate_time_score(db, user2.id, window_days=30)
        time_score = time_result.overall_score if time_result else 50
        
        print(f"   Calculated scores - Financial: {financial_score}, Health: {health_score}, Time: {time_score}")
        db.add(VivIndex(user_id=user2.id, financial_score=financial_score, health_score=health_score, time_score=time_score))
        db.commit()

        # 3. Health User
        print("3️⃣  Health User")
        user3 = create_base_user("user-health", "health@helm.com", "Health User", "Athlete", "Training.")
        seed_rich_health_data(user3.id)
        seed_minimal_finance_data(user3.id)
        seed_minimal_time_data(user3.id)
        
        # Health User: Fitness focused, modest income, prioritizes wellness over wealth
        health_onboarding = {
            "monthly_income": 4500,  # Gym trainer/fitness coach income
            "monthly_bills": 1400,
            "discretionary_spend": 900,  # Meal prep, supplements
            "monthly_savings": 600,  # Lower savings rate
            "cash_balance": 8000,  # Smaller emergency fund
            "investments_value": 12000,  # Minimal retirement
            "monthly_debt_payments": 150  # Student loans
        }
        
        fin3 = calculate_financial_health_score(user3.id, health_onboarding, db, is_manual_mode=False)
        health3 = calculate_health_score(user3.id, {}, db)
        time3 = calculate_time_score(db, user3.id, window_days=30)
        
        db.add(VivIndex(
            user_id=user3.id,
            financial_score=fin3.get("overall_score", 50),
            health_score=health3.get("score", 88) if isinstance(health3, dict) else 88,
            time_score=time3.overall_score if time3 else 50
        ))
        db.commit()

        # 4. Time User
        print("4️⃣  Time User")
        user4 = create_base_user("user-time", "time@helm.com", "Time User", "Pro", "Productivity.")
        seed_rich_time_data(user4.id)
        seed_minimal_finance_data(user4.id)
        seed_minimal_health_data(user4.id)
        
        # Time User: High earner, workaholic, sacrifices health for productivity
        time_onboarding = {
            "monthly_income": 12000,  # Tech exec/consultant
            "monthly_bills": 2500,  # Premium apartment, car lease
            "discretionary_spend": 2000,  # Eats out, premium services
            "monthly_savings": 2500,  # Good savings rate
            "cash_balance": 25000,  # Strong emergency fund
            "investments_value": 80000,  # Maxing 401k
            "monthly_debt_payments": 0  # Debt-free
        }
        
        fin4 = calculate_financial_health_score(user4.id, time_onboarding, db, is_manual_mode=False)
        health4 = calculate_health_score(user4.id, {}, db)
        time4 = calculate_time_score(db, user4.id, window_days=30)
        
        db.add(VivIndex(
            user_id=user4.id,
            financial_score=fin4.get("overall_score", 50),
            health_score=health4.get("score", 50) if isinstance(health4, dict) else 50,
            time_score=time4.overall_score if time4 else 82
        ))
        db.commit()

        # 5. Super User
        print("5️⃣  Super User")
        user5 = create_base_user("user-super", "super@helm.com", "Super User", "Legend", "All stars.")
        seed_rich_finance_data(user5.id)
        seed_rich_health_data(user5.id)
        seed_rich_time_data(user5.id)
        
        # Super User: Balanced excellence across all pillars
        super_onboarding = {
            "monthly_income": 15000,  # Senior exec/entrepreneur
            "monthly_bills": 2000,  # Reasonable housing
            "discretionary_spend": 1500,  # Controlled spending
            "monthly_savings": 4000,  # 26% savings rate
            "cash_balance": 50000,  # 6+ months emergency fund
            "investments_value": 250000,  # Diversified portfolio
            "monthly_debt_payments": 0  # Debt-free
        }
        
        fin5 = calculate_financial_health_score(user5.id, super_onboarding, db, is_manual_mode=False)
        health5 = calculate_health_score(user5.id, {}, db)
        time5 = calculate_time_score(db, user5.id, window_days=30)
        
        db.add(VivIndex(
            user_id=user5.id,
            financial_score=fin5.get("overall_score", 92),
            health_score=health5.get("score", 95) if isinstance(health5, dict) else 95,
            time_score=time5.overall_score if time5 else 89
        ))
        db.commit()

        print("\n✅ SEEDING COMPLETE!")

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\n❌ Seeding Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    safe_seed_users()
