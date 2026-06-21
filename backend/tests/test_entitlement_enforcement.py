import sys
import os
from unittest.mock import MagicMock
import datetime

# 1. Mock critical cloud/missing dependencies
sys.modules["google.cloud"] = MagicMock()
sys.modules["google.cloud.sql"] = MagicMock()
sys.modules["google.cloud.sql.connector"] = MagicMock()
sys.modules["pg8000"] = MagicMock()
sys.modules["jose"] = MagicMock()
mock_connector = MagicMock()
sys.modules["google.cloud.sql.connector"].Connector = MagicMock(
    return_value=mock_connector
)

# 2. Setup Path
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "backend")))

# 3. Create Memory Engine
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.declarative import declarative_base

TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
Base = declarative_base()


# 4. Patch Check - reuse logic from previous tests
class DummyDBModule:
    engine = test_engine
    SessionLocal = TestingSessionLocal
    Base = Base

    def get_db(self):
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    def init_db(self):
        pass


dummy_db = DummyDBModule()
sys.modules["models.database"] = dummy_db
sys.modules["backend.models.database"] = dummy_db

import backend.models

sys.modules["models"] = backend.models
import backend.models.models

sys.modules["models.models"] = backend.models.models
import backend.models.growth_models

sys.modules["models.growth_models"] = backend.models.growth_models
import backend.models.logging_models

sys.modules["models.logging_models"] = backend.models.logging_models


# Patch middleware again
async def mock_dispatch(self, request, call_next):
    return await call_next(request)


try:
    import backend.core.middleware

    backend.core.middleware.BugReportMiddleware.dispatch = mock_dispatch
except ImportError:
    pass
try:
    import core.middleware

    core.middleware.BugReportMiddleware.dispatch = mock_dispatch
except ImportError:
    pass

# Create Tables
Base.metadata.create_all(bind=test_engine)

from fastapi.testclient import TestClient
from backend.app import create_app
from backend.core.authentication import get_current_user

try:
    from core.authentication import get_current_user as get_current_user_legacy
except ImportError:
    get_current_user_legacy = None
from backend.models.models import User


# Mock Auth
def mock_get_current_user():
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == "test_force@helm.com").first()
        if not user:
            user = User(email="test_force@helm.com", id="user_force_test")
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    finally:
        db.close()


app = create_app()
app.dependency_overrides[get_current_user] = mock_get_current_user
if get_current_user_legacy:
    app.dependency_overrides[get_current_user_legacy] = mock_get_current_user
client = TestClient(app)


def test_goal_limit_enforcement():
    print("--- Starting Entitlement Enforcement Test ---")

    # 1. Create 5 Goals (Allowed on Free)
    for i in range(5):
        resp = client.post(
            "/api/finance/goals",
            json={
                "title": f"Goal {i+1}",
                "target_amount": 1000,
                "target_date": "2025-12-31T00:00:00",
            },
        )
        assert (
            resp.status_code == 200
        ), f"Failed to create allowed goal {i+1}: {resp.text}"
        print(f"Created Goal {i+1}")

    # 2. Try to Create 6th Goal (Should Fail)
    print("Attempting to create 6th goal (Expected Failure)...")
    resp_fail = client.post(
        "/api/finance/goals", json={"title": "Goal 6", "target_amount": 1000}
    )

    if resp_fail.status_code == 403:
        print("✅ Correctly rejected 6th goal with 403 Forbidden.")
        data = resp_fail.json()
        assert data["detail"]["code"] == "LIMIT_REACHED"
        print(f"Error Message Verified: {data['detail']['message']}")
    else:
        print(f"❌ Failed! Expected 403, got {resp_fail.status_code}: {resp_fail.text}")
        sys.exit(1)

    # 3. Upgrade to Pro
    print("Upgrading user to Pro...")
    resp_sub = client.post(
        "/api/growth/subscribe",
        json={"plan_id": "tier_pro", "payment_method_id": "pm_card"},
    )
    assert resp_sub.status_code == 200
    print("Upgrade Successful.")

    # 4. Try to Create 6th Goal Again (Should Success)
    print("Attempting to create 6th goal again (Expected Success)...")
    resp_success = client.post(
        "/api/finance/goals", json={"title": "Goal 6 (Pro)", "target_amount": 1000}
    )

    if resp_success.status_code == 200:
        print("✅ Correctly allowed 6th goal after upgrade.")
    else:
        print(
            f"❌ Failed! Expected 200, got {resp_success.status_code}: {resp_success.text}"
        )
        sys.exit(1)


if __name__ == "__main__":
    try:
        test_goal_limit_enforcement()
        print("--- ALL TESTS PASSED ---")
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
