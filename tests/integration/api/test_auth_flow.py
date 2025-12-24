
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app import create_app
from models.database import get_db, Base, engine
from models.models import User
from core.authentication import get_password_hash

# Setup Test App and DB
@pytest.fixture(scope="module")
def test_app():
    # Use a separate test DB or mocking if possible, but for now using the main one carefully
    # ideally we use an in-memory sqlite for tests
    app = create_app()
    return app

@pytest.fixture(scope="module")
def client(test_app):
    return TestClient(test_app)

@pytest.fixture(scope="function")
def db_session():
    # Setup
    session = SessionLocal()
    yield session
    # Teardown
    session.close()

def test_auth_state_machine_flow(client, db_session):
    # 1. Create a fresh user via direct DB insertion (simulating signup)
    email = "test_auth_flow@example.com"
    password = "password123"
    
    # Clean up if exists
    existing = db_session.query(User).filter_by(email=email).first()
    if existing:
        db_session.delete(existing)
        db_session.commit()

    new_user = User(
        email=email,
        hashed_password=get_password_hash(password),
        profile_json={"name": "Test User"},
        onboarding_status="NOT_STARTED", # Initial state
        onboarding_step="welcome"
    )
    db_session.add(new_user)
    db_session.commit()
    user_id = new_user.id
    
    # Debug: Check if user exists in DB
    saved_user = db_session.query(User).filter_by(email=email).first()
    print(f"DEBUG: Saved user: {saved_user.email if saved_user else 'None'}")
    from core.config import get_settings
    print(f"DEBUG: DB URL: {get_settings().DATABASE_URL}")

    # 2. Login
    login_res = client.post("/api/auth/login", json={"username": email, "password": password})
    print(f"DEBUG: Login Status: {login_res.status_code}")
    if login_res.status_code != 200:
        print(f"DEBUG: Login Response: {login_res.text}")
    assert login_res.status_code == 200
    data = login_res.json()
    token = data["access_token"]
    assert data["user"]["onboarding_status"] == "NOT_STARTED"
    
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Check Session -> Should be Authenticated but Incomplete
    session_res = client.get("/api/auth/session", headers=headers)
    assert session_res.status_code == 200
    s_data = session_res.json()
    assert s_data["authenticated"] is True
    assert s_data["user"]["onboarding_status"] == "NOT_STARTED"

    # 4. Progress Onboarding
    prog_res = client.post(
        f"/api/users/{user_id}/onboarding/progress",
        headers=headers,
        json={"step": "financial-1"}
    )
    assert prog_res.status_code == 200
    
    # Check status update
    db_session.refresh(new_user)
    assert new_user.onboarding_status == "IN_PROGRESS"
    assert new_user.onboarding_step == "financial-1"

    # 5. Complete Onboarding
    comp_res = client.post(
        f"/api/users/{user_id}/onboarding/complete",
        headers=headers
    )
    assert comp_res.status_code == 200
    
    # Check status update
    db_session.refresh(new_user)
    assert new_user.onboarding_status == "COMPLETE"
    assert new_user.onboarding_step is None

    # 6. Check Session -> Should be COMPLETE
    final_session_res = client.get("/api/auth/session", headers=headers)
    assert final_session_res.json()["user"]["onboarding_status"] == "COMPLETE"

    # Cleanup
    db_session.delete(new_user)
    db_session.commit()
