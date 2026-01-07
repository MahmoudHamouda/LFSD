import logging
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from models.database import SessionLocal
from models.models import User
from core.seeding import seed_user_data  # Reusing the robust logic we built

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_live_users():
    """
    Seeds data for standard mock personas if they exist in the DB.
    This is intended to be run ONCE manually to populate data.
    """
    db = SessionLocal()
    try:
        personas = [
            {"email": "finance@helm.com", "profile": "finance"},
            {"email": "health@helm.com", "profile": "health"},
            {"email": "time@helm.com", "profile": "time"},
            {"email": "empty@helm.com", "profile": "empty"}
        ]

        logger.info("Starting live user seeding...")

        for p in personas:
            email = p["email"]
            profile = p["profile"]
            
            # Find user by email (must have logged in at least once or been created)
            user = db.query(User).filter(User.email == email).first()
            
            if not user:
                logger.warning(f"User {email} not found in DB. Have they logged in?")
                continue
            
            logger.info(f"Checking data for {email} ({user.id})...")
            
            # Use the core seeding logic (which checks if data exists first)
            success = seed_user_data(db, user.id, profile)
            
            if success:
                logger.info(f"✅ Users {email} seeded successfully.")
                db.commit()
            else:
                logger.info(f"ℹ️ User {email} already has data or failed.")
                
    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_live_users()
