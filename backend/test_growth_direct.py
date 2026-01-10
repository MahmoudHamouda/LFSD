import sys
import os
from datetime import datetime

# Setup path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Mock env
os.environ["ENV"] = "dev"

from models.database import SessionLocal
from services.growth_service import GrowthService

def test_direct():
    db = SessionLocal()
    user_id = "verify-user-123"
    print(f"Testing GrowthService.get_entitlements for {user_id}")
    try:
        res = GrowthService.get_entitlements(user_id, db)
        print(f"SUCCESS: {res}")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_direct()
