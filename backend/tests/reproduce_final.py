
import sys
import os
import asyncio
import logging

# Setup Logging to file
logging.basicConfig(filename='test_debug.log', level=logging.DEBUG)

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.models import Base, User, LifeGoal, VivIndex, VivLog
from services.gemini_service import GeminiService

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

def verify_goal():
    db = SessionLocal()
    try:
        user_id = "user-123"
        user = User(id=user_id, email="test@test.com", hashed_password="pw")
        db.add(user)
        db.commit()
        logging.info("User created.")

        service = GeminiService(db)
        
        # Mock Intent
        async def mock_extract(*args, **kwargs):
            return {"intent": "set_goal", "amount": 100.0, "goal_type": "savings"}
        service._extract_intent = mock_extract
        
        # Override extract_intent and load_viv_context to prevent side effects
        service._load_viv_context = lambda uid: {
            "viv_indexes": {"financial":50}, 
            "life_goals": [], 
            "crisis_mode": False
        }

        logging.info("Calling generate_response")
        history = [{"role": "user", "content": "save 100"}]
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(service.generate_response(history, {}))
        
        logging.info(f"Response: {response}")
        
        goal = db.query(LifeGoal).filter(LifeGoal.user_id == user_id).first()
        if goal:
            logging.info(f"SUCCESS: Goal {goal.id} found.")
            print("SUCCESS_GOAL")
        else:
            logging.error("FAILURE: No goal found.")
            
        viv_log = db.query(VivLog).filter(VivLog.user_id == user_id).first()
        if viv_log:
             logging.info(f"SUCCESS: Log {viv_log.id} found. Intent: {viv_log.user_intent}")
             print("SUCCESS_LOG")
        else:
             logging.error("FAILURE: No VivLog found.")
             print("FAILURE_LOG")
            
    except Exception as e:
        logging.error(f"Test Exception: {e}", exc_info=True)
        print(f"ERROR: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_goal()
