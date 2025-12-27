
import sys
import os
from dotenv import load_dotenv

# Add the root directory to sys.path to find 'backend'
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(root_dir)

# Load .env from root
load_dotenv(os.path.join(root_dir, '.env'))

from backend.models.database import SessionLocal
from backend.models.models import User, LifeGoal
from datetime import datetime, timedelta

def seed_goals():
    print("Starting goal seeding...")
    db = SessionLocal()
    try:
        print(f"Connecting to database: {db.bind.url}")
        user = db.query(User).filter(User.email == "finance@helm.com").first()
        if not user:
            print("User finance@helm.com not found. Checking all users...")
            all_users = db.query(User).all()
            print(f"Total users in DB: {len(all_users)}")
            for u in all_users:
                print(f"- {u.email}")
            return

        print(f"Found user: {user.email} (ID: {user.id})")

        # Clear existing goals for this user to avoid duplicates if run multiple times
        deleted = db.query(LifeGoal).filter(LifeGoal.user_id == user.id).delete()
        print(f"Deleted {deleted} existing goals.")

        goals = [
            {
                "title": "Save $500 monthly for Emergency Fund",
                "target_amount": 6000.0,
                "saved_amount": 1200.0,
                "type": "emergency_fund",
                "monthly_contribution_target": 500.0,
                "priority": "high",
                "impact_vector_json": {"finance": 10, "health": 5, "time": 0}
            },
            {
                "title": "Deep Work: 4h Daily Focus",
                "target_amount": 120.0,
                "saved_amount": 45.0,
                "type": "custom",
                "monthly_contribution_target": 120.0,
                "priority": "medium",
                "impact_vector_json": {"time": 20, "finance": 5, "health": -2}
            },
            {
                "title": "Achieve 8h Average Sleep",
                "target_amount": 8.0,
                "saved_amount": 6.8,
                "type": "custom",
                "monthly_contribution_target": 8.0,
                "priority": "high",
                "impact_vector_json": {"health": 25, "time": 10, "finance": 0}
            }
        ]

        for g_data in goals:
            goal = LifeGoal(
                user_id=user.id,
                title=g_data["title"],
                target_amount=g_data["target_amount"],
                saved_amount=g_data["saved_amount"],
                target_date=datetime.utcnow() + timedelta(days=365),
                type=g_data["type"],
                monthly_contribution_target=g_data["monthly_contribution_target"],
                priority=g_data["priority"],
                impact_vector_json=g_data["impact_vector_json"]
            )
            db.add(goal)
        
        db.commit()
        print(f"Successfully seeded {len(goals)} goals for {user.email}")

    except Exception as e:
        print(f"Error seeding goals: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_goals()
