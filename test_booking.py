import asyncio
import os
from cryptography.fernet import Fernet
os.environ["DATABASE_URL"] = "sqlite:///./backend/lfsd.db"
os.environ["GOOGLE_MAPS_API_KEY"] = "mock"
os.environ["CREDENTIALS_ENCRYPTION_KEY"] = Fernet.generate_key().decode()

from backend.models import database
database.init_db()
db = database.SessionLocal()
from backend.services.gemini_service import GeminiService

async def test():
    gs = GeminiService(db)
    
    print("Test 1: price check with no provider")
    req1 = {"intent": "mobility_booking", "entities": {"destination": "airport", "start_location": "hotel", "provider": None, "ride_type": None}}
    try:
        ans = await gs._handle_mobility_request(req1, {}, "user123")
        print("Ans1:", ans)
    except Exception as e:
        import traceback
        traceback.print_exc()

    print("\nTest 2: booking check with provider")
    req2 = {"intent": "mobility_booking", "entities": {"destination": "airport", "start_location": "hotel", "provider": "uber", "ride_type": "x"}}
    try:
        ans = await gs._handle_mobility_request(req2, {}, "user123")
        print("Ans2:", ans)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
