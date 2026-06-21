"""
Safe Development Data Seeder

Creates 5 test personas with realistic data for local development.
CRITICAL: This script is ONLY for local/dev environments.
"""

import sys
import os
import random
from datetime import datetime, timedelta, timezone
import uuid

from models.database import SessionLocal, engine, Base
from models.models import (
    User,
    FinancialAccount,
    FinancialTransaction,
    VivIndex,
    HealthDailySummary,
    SleepSession,
    Workout,
    CalendarEvent,
    MobilityTrip,
    LifeGoal,
    FinancialScore,
    TimeProfile,
    TimeScore,
    HealthProfile,
)
from core.authentication import get_password_hash
from core.config import get_settings
from sqlalchemy import text

# ============================================================================
# ENVIRONMENT SAFETY GUARDS
# ============================================================================

settings = get_settings()

# CRITICAL: Block production
if settings.ENV == "prod" or settings.ENV == "production":
    print("🚨 ERROR: This script cannot run in production!")
    print("   Set ENV=dev or ENV=local to proceed.")
    sys.exit(1)

print(f"✅ Environment check passed: {settings.ENV}")
print(f"   Database: {settings.DATABASE_URL[:30]}...")

# Confirm destructive operation
print("\n⚠️  WARNING: This will DELETE ALL DATA and recreate tables!")
response = input("Type 'DELETE_ALL' to continue: ")
if response != "DELETE_ALL":
    print("❌ Operation cancelled.")
    sys.exit(0)

# ============================================================================
# SETUP
# ============================================================================

db = SessionLocal()
PASSWORD_HASH = get_password_hash("P@ssword123")


def random_date(start_days_ago=90, end_days_ago=0):
    """Generate random datetime within range"""
    start = datetime.now(timezone.utc) - timedelta(days=start_days_ago)
    end = datetime.now(timezone.utc) - timedelta(days=end_days_ago)
    return start + (end - start) * random.random()


# ============================================================================
# DATABASE RESET
# ============================================================================


def clean_database():
    """Drop and recreate all tables - DESTRUCTIVE"""
    print("\n🗑️  Cleaning database...")
    try:
        # Drop all tables with CASCADE
        print("   Dropping all tables...")
        for table in reversed(Base.metadata.sorted_tables):
            try:
                db.execute(text(f"DROP TABLE IF EXISTS {table.name} CASCADE;"))
            except Exception as e:
                print(f"   ⚠️  Warning dropping {table.name}: {e}")
        db.commit()

        # Create tables
        print("   Creating tables...")
        Base.metadata.create_all(bind=engine)

        print("   ✅ Database cleaned successfully")

    except Exception as e:
        print(f"   ❌ Error cleaning database: {e}")
        db.rollback()
        raise


# ============================================================================
# USER CREATION
# ============================================================================


def create_base_user(user_id, email, name, persona_type, bio):
    """Create a base user with common fields"""
    print(f"   Creating {name} ({email})...")
    user = User(
        id=user_id,
        email=email,
        hashed_password=PASSWORD_HASH,
        profile_json={"name": name, "type": persona_type, "bio": bio},
        viv_preferences={"risk_tolerance": "medium"},
        onboarding_status="COMPLETED",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ============================================================================
# RICH DATA SEEDING (90 Days + Goals + Trends)
# ============================================================================


def seed_rich_finance_data(user_id):
    """Seed 90 days of financial data with realistic patterns"""
    print(f"      💰 Seeding rich financial data...")

    # Accounts
    checking = FinancialAccount(
        user_id=user_id,
        institution_name="Chase",
        account_type="checking",
        current_balance=12500.00,
    )
    savings = FinancialAccount(
        user_id=user_id,
        institution_name="Ally",
        account_type="savings",
        current_balance=45000.00,
    )
    credit_card = FinancialAccount(
        user_id=user_id,
        institution_name="Amex",
        account_type="credit",
        current_balance=-1200.00,
        limit=15000.0,
    )
    db.add_all([checking, savings, credit_card])
    db.commit()

    # Transactions (90 days with realistic patterns)
    start_date = datetime.now(timezone.utc) - timedelta(days=90)

    for day in range(90):
        current_date = start_date + timedelta(days=day)

        # Income (Bi-monthly salary on 15th and 30th)
        if current_date.day in [15, 30]:
            db.add(
                FinancialTransaction(
                    user_id=user_id,
                    account_id=checking.id,
                    amount=5000.0,
                    description="TechCorp Salary",
                    category_primary="Income",
                    transaction_date=current_date,
                )
            )

        # Rent (Monthly on 1st)
        if current_date.day == 1:
            db.add(
                FinancialTransaction(
                    user_id=user_id,
                    account_id=checking.id,
                    amount=-2500.0,
                    description="Rent Payment",
                    category_primary="Rent",
                    transaction_date=current_date,
                )
            )

        # Daily coffee (90% of days)
        if random.random() > 0.1:
            db.add(
                FinancialTransaction(
                    user_id=user_id,
                    account_id=credit_card.id,
                    amount=-random.uniform(5, 15),
                    description="Starbucks",
                    category_primary="Food",
                    transaction_date=current_date,
                )
            )

        # Weekly groceries (Saturdays)
        if current_date.weekday() == 5:
            db.add(
                FinancialTransaction(
                    user_id=user_id,
                    account_id=credit_card.id,
                    amount=-random.uniform(150, 300),
                    description="Whole Foods",
                    category_primary="Groceries",
                    transaction_date=current_date,
                )
            )

    # Life Goals
    db.add(
        LifeGoal(
            user_id=user_id,
            title="House Downpayment",
            target_amount=100000,
            saved_amount=45000,
            priority="high",
            pillar="finance",
            type="house",
            monthly_contribution_target=2000.0,
        )
    )
    db.add(
        LifeGoal(
            user_id=user_id,
            title="Emergency Fund",
            target_amount=20000,
            saved_amount=20000,
            priority="medium",
            pillar="finance",
            type="emergency_fund",
        )
    )

    # Financial Scores (trending upward)
    for i in range(12):
        db.add(
            FinancialScore(
                user_id=user_id,
                overall_score=75 + (i * 0.5),
                timestamp=datetime.now(timezone.utc) - timedelta(weeks=12 - i),
            )
        )
    db.commit()


def seed_rich_health_data(user_id):
    """Seed 90 days of health data with realistic activity"""
    print(f"      💪 Seeding rich health data...")

    start_date = datetime.now(timezone.utc) - timedelta(days=90)
    for day in range(90):
        current_date = start_date + timedelta(days=day)

        is_weekend = current_date.weekday() >= 5
        steps = (
            random.randint(8000, 15000)
            if not is_weekend
            else random.randint(12000, 20000)
        )

        db.add(
            HealthDailySummary(
                user_id=user_id,
                date=current_date.date(),
                sleep_duration_minutes=random.randint(420, 540),
                sleep_quality_score=random.uniform(75, 95),
                steps_count=steps,
                hrv_average=random.uniform(55, 90),
                resting_heart_rate=random.randint(45, 60),
            )
        )

    # Workouts (~3x per week)
    for i in range(40):
        start = random_date(90, 0)
        db.add(
            Workout(
                user_id=user_id,
                start_time=start,
                end_time=start + timedelta(minutes=60),
                activity_type=random.choice(["CrossFit", "Running", "Cycling"]),
                calories_burned=random.randint(400, 800),
            )
        )

    # Health Goals
    db.add(
        LifeGoal(
            user_id=user_id,
            title="Boston Marathon Qualify",
            target_amount=100,
            saved_amount=75,
            priority="high",
            pillar="health",
            type="fitness",
            impact_vector_json={"health": 100},
        )
    )

    db.add(
        HealthProfile(
            user_id=user_id,
            diet_style="Paleo",
            water_intake_range="3L+",
            activity_self_report="Athlete",
            stress_level="Low",
        )
    )
    db.commit()


def seed_rich_time_data(user_id):
    """Seed 90 days of calendar and time management data"""
    print(f"      📅 Seeding rich time data...")

    start_date = datetime.now(timezone.utc) - timedelta(days=90)
    for day in range(90):
        current_date = start_date + timedelta(days=day)

        if current_date.weekday() < 5:  # Weekdays
            # Daily Standup
            db.add(
                CalendarEvent(
                    user_id=user_id,
                    title="Daily Standup",
                    start_time=current_date.replace(hour=9, minute=0),
                    end_time=current_date.replace(hour=9, minute=30),
                    is_meeting=True,
                    location_context="office",
                )
            )
            # Focus Block
            db.add(
                CalendarEvent(
                    user_id=user_id,
                    title="Deep Work Block",
                    start_time=current_date.replace(hour=10, minute=0),
                    end_time=current_date.replace(hour=12, minute=0),
                    is_meeting=False,
                    location_context="office",
                )
            )
            # Some random meetings (50% chance)
            if random.random() > 0.5:
                db.add(
                    CalendarEvent(
                        user_id=user_id,
                        title="Project Sync",
                        start_time=current_date.replace(hour=14, minute=0),
                        end_time=current_date.replace(hour=15, minute=0),
                        is_meeting=True,
                        location_context="office",
                    )
                )

    # Time Goals
    db.add(
        LifeGoal(
            user_id=user_id,
            title="Limit Meetings to 10h/week",
            target_amount=10,
            saved_amount=12,
            priority="medium",
            pillar="time",
            type="productivity",
        )
    )

    db.add(
        TimeProfile(
            user_id=user_id,
            work_hours_per_week="45",
            time_overwhelm_level="Low",
            task_style="Time Blocking",
        )
    )

    # Time Scores
    for i in range(12):
        db.add(
            TimeScore(
                user_id=user_id,
                overall_score=80 + random.uniform(-2, 2),
                timestamp=datetime.now(timezone.utc) - timedelta(weeks=12 - i),
            )
        )
    db.commit()


# ============================================================================
# MINIMAL DATA SEEDING (14 Days - bare minimum for calculations)
# ============================================================================


def seed_minimal_finance_data(user_id):
    """Minimal financial data for basic score calculation"""
    checking = FinancialAccount(
        user_id=user_id,
        institution_name="SimpleBank",
        account_type="checking",
        current_balance=2000.0,
    )
    db.add(checking)
    db.commit()

    for i in range(14):
        db.add(
            FinancialTransaction(
                user_id=user_id,
                account_id=checking.id,
                amount=-5.0,
                description="Coffee",
                category_primary="Food",
                transaction_date=datetime.now(timezone.utc) - timedelta(days=i),
            )
        )

    db.add(
        FinancialScore(
            user_id=user_id, overall_score=50, timestamp=datetime.now(timezone.utc)
        )
    )
    db.commit()


def seed_minimal_health_data(user_id):
    """Minimal health data for basic score calculation"""
    for i in range(14):
        db.add(
            HealthDailySummary(
                user_id=user_id,
                date=(datetime.now(timezone.utc) - timedelta(days=i)).date(),
                steps_count=5000,
                sleep_duration_minutes=400,
            )
        )
    db.add(HealthProfile(user_id=user_id, diet_style="None"))
    db.commit()


def seed_minimal_time_data(user_id):
    """Minimal time data for basic score calculation"""
    for i in range(5):
        start = datetime.now(timezone.utc) - timedelta(days=i)
        db.add(
            CalendarEvent(
                user_id=user_id,
                title="Work",
                start_time=start,
                end_time=start + timedelta(hours=8),
                is_meeting=False,
            )
        )
    db.add(TimeProfile(user_id=user_id, work_hours_per_week="40"))
    db.commit()


# ============================================================================
# MAIN EXECUTION
# ============================================================================


def populate_synthetic_data():
    """Main seeding function - creates 5 test personas"""
    try:
        clean_database()

        print("\n🌱 Seeding test personas...\n")

        # 1. Empty User
        print("1️⃣  Empty User (new signup)")
        user1 = create_base_user(
            "user-empty", "empty@helm.com", "Empty User", "Newbie", "Just joined."
        )
        user1.onboarding_status = "NOT_STARTED"
        db.commit()

        # 2. Finance-Focused User
        print("2️⃣  Finance User (rich financial data)")
        user2 = create_base_user(
            "user-finance",
            "finance@helm.com",
            "Finance User",
            "Planner",
            "Focused on wealth building.",
        )
        seed_rich_finance_data(user2.id)
        seed_minimal_health_data(user2.id)
        seed_minimal_time_data(user2.id)
        db.add(
            VivIndex(
                user_id=user2.id, financial_score=85, health_score=50, time_score=50
            )
        )
        db.commit()

        # 3. Health-Focused User
        print("3️⃣  Health User (rich health data)")
        user3 = create_base_user(
            "user-health",
            "health@helm.com",
            "Health User",
            "Athlete",
            "Marathon training.",
        )
        seed_rich_health_data(user3.id)
        seed_minimal_finance_data(user3.id)
        seed_minimal_time_data(user3.id)
        db.add(
            VivIndex(
                user_id=user3.id, financial_score=50, health_score=88, time_score=50
            )
        )
        db.commit()

        # 4. Time-Focused User
        print("4️⃣  Time User (rich productivity data)")
        user4 = create_base_user(
            "user-time",
            "time@helm.com",
            "Time User",
            "Productivity Expert",
            "Calendar optimization master.",
        )
        seed_rich_time_data(user4.id)
        seed_minimal_finance_data(user4.id)
        seed_minimal_health_data(user4.id)
        db.add(
            VivIndex(
                user_id=user4.id, financial_score=50, health_score=50, time_score=82
            )
        )
        db.commit()

        # 5. Super User (all data)
        print("5️⃣  Super User (all pillars rich)")
        user5 = create_base_user(
            "user-super",
            "super@helm.com",
            "Super User",
            "Legend",
            "Excelling in all areas.",
        )
        seed_rich_finance_data(user5.id)
        seed_rich_health_data(user5.id)
        seed_rich_time_data(user5.id)
        db.add(
            VivIndex(
                user_id=user5.id, financial_score=92, health_score=95, time_score=89
            )
        )
        db.commit()

        print("\n✅ Successfully seeded 5 test personas!")
        print("\n📧 Login credentials for all users:")
        print("   Password: P@ssword123")
        print("\n   Emails:")
        print("   - empty@helm.com (no data)")
        print("   - finance@helm.com (rich finance)")
        print("   - health@helm.com (rich health)")
        print("   - time@helm.com (rich time)")
        print("   - super@helm.com (all rich)")

    except Exception as e:
        import traceback

        traceback.print_exc()
        print(f"\n❌ Error seeding data: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    populate_synthetic_data()
