import sys
import os
import asyncio
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from models.models import Base, User, DBConversation, DBMessage, DBActivity
from services.gemini_service import GeminiService
from services.growth_service import GrowthService

# Setup Test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

async def test_usage_tracking():
    db = SessionLocal()
    try:
        # 1. Setup User
        user_id = "test-user-usage"
        user = User(id=user_id, email="usage@test.com", hashed_password="pw")
        db.add(user)
        db.commit()
        print(f"Created user: {user_id}")

        # 2. Mock Gemini Service to return usage
        service = GeminiService(db)
        
        # We need a mock response object that has usage_metadata
        class MockUsage:
            def __init__(self):
                self.prompt_token_count = 10
                self.candidates_token_count = 20

        class MockResponse:
            def __init__(self):
                self.text = '{"summary": "Test", "message_body": "Hello", "viv_indexes": {}, "usage": {"input_tokens": 10, "output_tokens": 20}}'
                self.usage_metadata = MockUsage()

        async def mock_generate(*args, **kwargs):
            return MockResponse()
        
        service._generate_content_safe = mock_generate
        service.model_name = "gemini-1.5-flash"

        # 3. Simulate Chat Interaction (mimicking api_routes_history.py logic)
        print("Simulating Gemini Interaction...")
        history = [{"role": "user", "content": "hello"}]
        
        # Normally this is in the route, we'll manually simulate it
        response = await service.generate_response(history, {"user_id": user_id})
        response_data = json.loads(response)
        content = response_data.get('text', '')
        usage = response_data.get('usage', {})
        
        print(f"Gemini Response Usage: {usage}")

        # Save to DB (as done in routes)
        conv_id = "conv-1"
        conv = DBConversation(id=conv_id, user_id=user_id, title="Test", date=datetime.utcnow())
        db.add(conv)
        
        msg = DBMessage(
            id="msg-1",
            conversation_id=conv_id,
            user_id=user_id,
            role="assistant",
            content=content,
            input_tokens=usage.get('input_tokens', 0),
            output_tokens=usage.get('output_tokens', 0),
            model_used="gemini-1.5-flash"
        )
        db.add(msg)
        
        activity = DBActivity(
            user_id=user_id,
            type="GEMINI_USAGE_RECORDED",
            description="Test usage",
            metadata_json=json.dumps(usage)
        )
        db.add(activity)
        db.commit()

        # 4. Verify Growth Service aggregation
        print("Verifying Growth Service Entitlements...")
        entitlements = GrowthService.get_entitlements(user_id, db)
        print(f"Usage Stats: {entitlements.usage}")
        
        if entitlements.usage.get("total_tokens_month") == 30:
            print("✅ SUCCESS: Token usage aggregated correctly (30 tokens)!")
        else:
            print(f"❌ FAILURE: Expected 30 tokens, got {entitlements.usage.get('total_tokens_month')}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    from datetime import datetime
    asyncio.run(test_usage_tracking())
