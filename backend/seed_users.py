from models.database import engine, SessionLocal
from models.models import User, HealthDailySummary, Connection, VivIndex, LifeGoal, FinancialAccount, Transaction, SleepSession, Workout, CalendarEvent, MobilityTrip, VivLog, DBConversation, DBMessage
from sqlalchemy.orm import configure_mappers
configure_mappers()
from core.authentication import get_password_hash

def seed_users():
    db = SessionLocal()
    try:
        # Check if alice exists
        user = db.query(User).filter(User.email == "alice@example.com").first()
        if not user:
            print("Creating user 'alice'...")
            user = User(
                id="user-123", # Match ID from core/authentication.py
                email="alice@example.com",
                hashed_password=get_password_hash("password"),
                profile_json={"name": "Alice"}
            )
            db.add(user)
            db.commit()
            print("User 'alice' created.")
        else:
            print("User 'alice' already exists.")
    except Exception as e:
        print(f"Error seeding users: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_users()
