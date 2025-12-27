import sys
import os
import random
from datetime import datetime, timedelta
import uuid

# Add parent directory to path to allow importing from models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import SessionLocal
from models.models import (
    User, FinancialAccount, Transaction, VivIndex, Connection,
    HealthDailySummary, CalendarEvent, SleepSession
)
from core.authentication import get_password_hash

def generate_uuid():
    return str(uuid.uuid4())

def seed_qa_users():
    db = SessionLocal()
    password_hash = get_password_hash("password") # Default password for all
    
    users_config = [
        {
            "id": "qa-user-a",
            "email": "qa_user_a@test.com",
            "name": "User A (Empty)",
            "type": "A"
        },
        {
            "id": "qa-user-b",
            "email": "qa_user_b@test.com",
            "name": "User B (Finance Only)",
            "type": "B"
        },
        {
            "id": "qa-user-c",
            "email": "qa_user_c@test.com",
            "name": "User C (All Connected)",
            "type": "C"
        }
    ]

    print("Seeding QA Users...")
    
    try:
        for u_cfg in users_config:
            # Cleanup existing
            existing = db.query(User).filter(User.email == u_cfg["email"]).first()
            if existing:
                print(f"Deleting existing {u_cfg['name']}...")
                db.delete(existing)
            
            # Create User
            print(f"Creating {u_cfg['name']}...")
            user = User(
                id=u_cfg["id"],
                email=u_cfg["email"],
                hashed_password=password_hash,
                profile_json={"name": u_cfg["name"], "type": "QA_Test_User"},
                viv_preferences={"risk_tolerance": "medium"},
                onboarding_status="COMPLETE"
            )
            db.add(user)
            db.commit() # Commit user first to satisfy foreign keys

            # ====================================================
            # USER A: No Connections (Done)
            # ====================================================
            if u_cfg["type"] == "A":
                continue

            # ====================================================
            # USER B & C: Finance
            # ====================================================
            if u_cfg["type"] in ["B", "C"]:
                # Connection
                db.add(Connection(
                    user_id=user.id,
                    provider="bank_simul",
                    status="connected",
                    metadata_json='{"bank_name": "QA Bank"}'
                ))
                
                # Account
                account_id = generate_uuid()
                db.add(FinancialAccount(
                    id=account_id,
                    user_id=user.id,
                    institution_name="QA Bank",
                    account_type="checking",
                    current_balance=12500.0,
                    limit=0.0
                ))
                
                # Transactions (Last 30 days)
                cats = [
                    ("Food & Drink", "Restaurants", 50, 150),
                    ("Groceries", "Supermarket", 100, 300),
                    ("Transport", "Uber", 20, 60),
                    ("Shopping", "Online", 50, 200),
                    ("Utilities", "Electric", 100, 150)
                ]
                
                for i in range(30):
                    date = datetime.utcnow() - timedelta(days=i)
                    # Daily spend
                    for _ in range(random.randint(1, 3)):
                        cat = random.choice(cats)
                        amt = random.uniform(cat[2], cat[3])
                        db.add(Transaction(
                            id=generate_uuid(),
                            account_id=account_id,
                            user_id=user.id,
                            amount=amt,
                            currency_code="EGP",
                            transaction_date=date,
                            description=f"QA Transaction {cat[1]}",
                            category_primary=cat[0],
                            category_detailed=cat[1]
                        ))
                
                # Income
                db.add(Transaction(
                    id=generate_uuid(),
                    account_id=account_id,
                    user_id=user.id,
                    amount=-25000.0, # Negative for credit? Or strictly 'amount'? USUALLY income is negative if debits are positive, or vice versa. Assuming standard: Debits +, Credits -.
                    # Wait, usually income is inflow. Let's check seed_data.py or assumption.
                    # seed_data used + for expense. So income likely negative or handled separately. 
                    # Let's assume standard bank csv: negative is outflow? 
                    # Actually, let's look at seed_data.py: "amount=12.50, category='Transport'". That's positive.
                    # So Expense = Positive. Income = Negative.
                    currency_code="EGP",
                    transaction_date=datetime.utcnow() - timedelta(days=15),
                    description="Salary Payment",
                    category_primary="Income",
                    category_detailed="Salary"
                ))

            # ====================================================
            # USER C: Health & Time
            # ====================================================
            if u_cfg["type"] == "C":
                # HEALTH
                db.add(Connection(
                    user_id=user.id,
                    provider="whoop",
                    status="connected"
                ))
                
                # 30 days of health data
                for i in range(30):
                    date = datetime.utcnow() - timedelta(days=i)
                    db.add(HealthDailySummary(
                        id=generate_uuid(),
                        user_id=user.id,
                        date=date.date(),
                        sleep_duration_minutes=random.randint(300, 480), # 5-8 hours
                        sleep_quality_score=random.uniform(50, 95),
                        steps_count=random.randint(2000, 12000),
                        resting_heart_rate=random.randint(50, 70),
                        hrv_average=random.randint(30, 80)
                    ))
                    # Sleep Session
                    sleep_start = date - timedelta(hours=8)
                    sleep_end = date
                    db.add(SleepSession(
                        id=generate_uuid(),
                        user_id=user.id,
                        start_time=sleep_start,
                        end_time=sleep_end,
                        deep_sleep_minutes=random.randint(40, 90),
                        rem_sleep_minutes=random.randint(60, 120),
                        wake_count=random.randint(0, 5)
                    ))

                # TIME / CALENDAR
                db.add(Connection(
                    user_id=user.id,
                    provider="google_calendar",
                    status="connected"
                ))
                
                # Future events for "Scheduler" tests
                for i in range(7): # Next 7 days
                    date = datetime.utcnow() + timedelta(days=i)
                    # Work block
                    db.add(CalendarEvent(
                        id=generate_uuid(),
                        user_id=user.id,
                        start_time=date.replace(hour=9, minute=0),
                        end_time=date.replace(hour=17, minute=0),
                        title="Work",
                        is_meeting=False,
                        location_context="office"
                    ))
                    # Maybe a conflict
                    if i % 2 == 0:
                        db.add(CalendarEvent(
                            id=generate_uuid(),
                            user_id=user.id,
                            start_time=date.replace(hour=19, minute=0),
                            end_time=date.replace(hour=21, minute=0),
                            title="Dinner",
                            is_meeting=False,
                            location_context="home"
                        ))

            # indices (for all?)
            db.add(VivIndex(
                user_id=user.id,
                financial_score=75.0 if u_cfg["type"] != "A" else 0.0,
                health_score=80.0 if u_cfg["type"] == "C" else 0.0,
                time_score=60.0 if u_cfg["type"] == "C" else 0.0,
                timestamp=datetime.utcnow()
            ))
            
            db.commit()
            print(f"Seeded {u_cfg['name']} successfully.")

    except Exception as e:
        print(f"Error seeding QA users: {e}")
        db.rollback()
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_qa_users()
