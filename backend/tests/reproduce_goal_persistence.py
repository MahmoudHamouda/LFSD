import sys
import os
import asyncio
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from models.models import Base, User, LifeGoal, VivIndex
from services.gemini_service import GeminiService
from models.database import get_db

# Setup Test DB (Memory for speed/safety)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# CREATE TABLES
Base.metadata.create_all(bind=engine)


def verify_goal_persistence():
    db = SessionLocal()
    try:
        # 1. Setup User
        # NOTE: GeminiService hardcodes "user-123", so we MUST use that.
        test_user_id = "user-123"
        user = User(id=test_user_id, email="viv_test@example.com", hashed_password="pw")
        db.add(user)

        # Init Index to avoid context loading crash
        idx = VivIndex(
            id="idx-1",
            user_id=test_user_id,
            financial_score=50.0,
            health_score=50.0,
            time_score=50.0,
        )
        db.add(idx)

        db.commit()

        # 2. Initialize Service
        print("[SETUP] Initializing GeminiService")
        service = GeminiService(db)

        # 3. Simulate "Set Goal" Intent via Monkey Patching
        async def mock_extract(*args, **kwargs):
            return {"intent": "set_goal", "amount": 9999.0, "goal_type": "investment"}

        service._extract_intent = mock_extract

        # 4. Run generate_response
        print("[ACTION] Sending Goal Request...")
        history = [{"role": "user", "content": "Set an investment goal for 9999"}]

        loop = asyncio.get_event_loop()
        response_json = loop.run_until_complete(service.generate_response(history, {}))

        print(f"[RESULT] Service Response: {response_json}")

        # 5. Verify DB
        print("[VERIFY] Checking LifeGoal table...")
        goal = (
            db.query(LifeGoal)
            .filter(LifeGoal.user_id == test_user_id, LifeGoal.target_amount == 9999.0)
            .first()
        )

        if goal:
            print("✅ SUCCESS: Goal found in database!")
            print(f"   - Title: {goal.title}")
            print(f"   - Amount: {goal.target_amount}")
        else:
            print("❌ FAILURE: Goal NOT found in database.")
            goals = db.query(LifeGoal).all()
            print(f"   - Total Goals in DB: {len(goals)}")
            exit(1)

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    verify_goal_persistence()
