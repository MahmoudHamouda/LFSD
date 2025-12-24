
import sys
import os
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.join(os.getcwd(), 'backend'))

from models.models import Base, User, LifeGoal

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

def test_write():
    db = SessionLocal()
    try:
        user_id = "u1"
        db.add(User(id=user_id, email="x@x.com", hashed_password="x"))
        db.commit()
        
        goal = LifeGoal(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title="Test Goal",
            target_amount=100.0,
            type="savings",
            priority="medium",
            saved_amount=0.0
        )
        db.add(goal)
        db.commit()
        print("WRITE SUCCESS")
    except Exception as e:
        print(f"WRITE FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_write()
