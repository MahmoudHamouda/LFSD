import sys
from unittest.mock import MagicMock

# Mock Gemini and Google Cloud
mock_genai = MagicMock()
sys.modules["google.generativeai"] = mock_genai
sys.modules["google.cloud"] = MagicMock()
sys.modules["google.api_core"] = MagicMock()
sys.modules["google.auth"] = MagicMock()

import os
import json
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from models.models import Base, User, DBMessage, Recommendation, LifeGoal
from services.growth_service import GrowthService
from datetime import datetime

# Setup Test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

def test_growth_aggregation():
    db = SessionLocal()
    try:
        user_id = "test-growth-user"
        user = User(id=user_id, email="growth@test.com", hashed_password="pw")
        db.add(user)
        db.commit()
        
        # Add messages with tokens
        msg1 = DBMessage(
            id="m1", conversation_id="c1", user_id=user_id, role="user", content="hi",
            input_tokens=10, output_tokens=5, date=datetime.utcnow()
        )
        msg2 = DBMessage(
            id="m2", conversation_id="c1", user_id=user_id, role="assistant", content="hello",
            input_tokens=5, output_tokens=20, date=datetime.utcnow()
        )
        db.add_all([msg1, msg2])
        db.commit()
        
        print(f"Added messages with total tokens: {(10+5) + (5+20)} = 40")
        
        # We need to simulate the result because GrowthService might still have issues
        # But let's see if the mock worked and we can call it.
        entitlements = GrowthService.get_entitlements(user_id, db)
        print(f"Usage: {entitlements.usage}")
        
        if entitlements.usage.get("total_tokens_month") == 40:
            print("✅ SUCCESS: GrowthService summed tokens correctly!")
        else:
            print(f"❌ FAILURE: Expected 40, got {entitlements.usage.get('total_tokens_month')}")

    except Exception as e:
        print(f"❌ ERROR in test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_growth_aggregation()
