import sys
import os
import importlib
from unittest.mock import MagicMock

# 1. Mock critical cloud/missing dependencies
sys.modules["google.cloud"] = MagicMock()
sys.modules["google.cloud.sql"] = MagicMock()
sys.modules["google.cloud.sql.connector"] = MagicMock()
sys.modules["pg8000"] = MagicMock()
sys.modules["jose"] = MagicMock()
mock_connector = MagicMock()
sys.modules["google.cloud.sql.connector"].Connector = MagicMock(return_value=mock_connector)

# 2. Setup Path
# We want to force everything to use 'backend' as the top-level package where possible,
# BUT the existing code uses 'backend' in path.
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "backend")))

# 3. Create Memory Engine
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.declarative import declarative_base

TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
Base = declarative_base()

# 4. Patch 'models.database' (the one imported relative to backend root) and 'backend.models.database'
class DummyDBModule:
    engine = test_engine
    SessionLocal = TestingSessionLocal
    Base = Base
    def get_db(self):
        db = TestingSessionLocal()
        try: yield db 
        finally: db.close()
    def init_db(self): pass

dummy_db = DummyDBModule()
sys.modules["models.database"] = dummy_db
sys.modules["backend.models.database"] = dummy_db

# 5. Prevent double import of 'models'
# We import 'backend.models' and then alias 'models' to it.
import backend.models
sys.modules["models"] = backend.models

# We must also ensure submodules overlap.
# For every submodule of backend.models, alias it in models.
# This prevents 'from models import models' from loading a new file.
import backend.models.models
sys.modules["models.models"] = backend.models.models

import backend.models.growth_models
sys.modules["models.growth_models"] = backend.models.growth_models

import backend.models.logging_models
sys.modules["models.logging_models"] = backend.models.logging_models

# And so on for others if needed, but these are the core ones for now.
# Actually, let's proactively patch models.auth_schemas if it exists.
try:
    import backend.models.auth_schemas
    sys.modules["models.auth_schemas"] = backend.models.auth_schemas
except ImportError:
    pass

# 5b. Patch BugReportMiddleware to propagate exceptions
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

# 6. Create Tables
Base.metadata.create_all(bind=test_engine)

# 7. Import App
from fastapi.testclient import TestClient
from backend.app import create_app
from core.authentication import get_current_user # Base import path
from backend.models.models import User, DBMessage
from datetime import datetime

# Mock Auth
def mock_get_current_user():
    db = TestingSessionLocal()
    try:
        user = db.query(User).filter(User.email == "test_growth@helm.com").first()
        if not user:
            user = User(
                email="test_growth@helm.com", 
                id="user_growth_test",
                role="user"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    finally:
        db.close()

app = create_app()
app.dependency_overrides[get_current_user] = mock_get_current_user
client = TestClient(app)

def test_get_entitlements_free():
    # Ensure some usage exists
    db = TestingSessionLocal()
    user = mock_get_current_user()
    msg = DBMessage(
        id="msg_test_1",
        conversation_id="conv_test_1",
        user_id=user.id,
        role="user",
        content="Hello usage tracking",
        date=datetime.utcnow()
    )
    db.add(msg)
    db.commit()
    db.close()

    response = client.get("/api/growth/entitlements")
    assert response.status_code == 200, f"Failed: {response.text}"
    data = response.json()
    assert data["plan"] == "tier_free"
    assert data["limits"]["ai_chat_calls"] == 100
    assert data["usage"]["ai_chat_calls"] >= 1, f"Usage should be at least 1, got {data.get('usage')}"

def test_subscribe_plus():
    response = client.post("/api/growth/subscribe", json={"plan_id": "tier_plus", "payment_method_id": "pm_test"})
    assert response.status_code == 200, f"Failed: {response.text}"
    
    resp_ent = client.get("/api/growth/entitlements")
    data_ent = resp_ent.json()
    assert data_ent["plan"] == "tier_plus"
    assert data_ent["limits"]["ai_chat_calls"] == 500
    assert data_ent["limits"]["smart_recos"] == 100
    assert data_ent["limits"]["executions"] == 20

def test_subscribe_pro():
    response = client.post("/api/growth/subscribe", json={"plan_id": "tier_pro", "payment_method_id": "pm_test"})
    assert response.status_code == 200, f"Failed: {response.text}"
    
    resp_ent = client.get("/api/growth/entitlements")
    data_ent = resp_ent.json()
    assert data_ent["plan"] == "tier_pro"
    assert data_ent["limits"]["ai_chat_calls"] == 2000
    assert data_ent["limits"]["smart_recos"] == 500
    assert data_ent["limits"]["executions"] == 100

if __name__ == "__main__":
    try:
        test_get_entitlements_free()
        print("test_get_entitlements_free PASSED")
        test_subscribe_plus()
        print("test_subscribe_plus PASSED")
        test_subscribe_pro()
        print("test_subscribe_pro PASSED")
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
