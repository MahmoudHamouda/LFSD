import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from models.models import User, VivIndex
from services.recommendation_service.treat_engine import compute_treats
from core.config import get_settings

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def verify_treats(email):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"❌ User {email} not found.")
            return

        print(f"✅ User found: {user.id}")
        
        # 1. Clear old indexes to avoid noise
        db.query(VivIndex).filter(VivIndex.user_id == user.id).delete()
        
        # 2. Seed High Scores
        high_index = VivIndex(
            user_id=user.id,
            financial_score=85,
            health_score=90,
            time_score=82,
            timestamp=datetime.utcnow()
        )
        db.add(high_index)
        db.commit()
        print("✅ Seeded high scores (Fin: 85, Health: 90, Time: 82)")
        
        # 3. Call Treat Engine
        treats = compute_treats(user.id, db)
        print(f"\nComputed Treats: {len(treats)}")
        for t in treats:
            print(f"  - [{t['category']}] {t['title']}: {t['body']}")
            
        expected_count = 3
        if len(treats) == expected_count:
            print(f"\n✅ PASS: Found {expected_count} treats.")
        else:
            print(f"\n❌ FAIL: Expected {expected_count} treats, but found {len(treats)}.")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    verify_treats("finance@helm.com")
