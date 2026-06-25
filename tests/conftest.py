import pytest
import sys
import os
# Define safe environment defaults for testing
os.environ.setdefault("CREDENTIALS_ENCRYPTION_KEY", "yTA972sJDSyacuu6_DPuibR412Mqp4g-iaerwubc8DU=")
os.environ.setdefault("SECRET_KEY", "test_secret_key_for_signing_tokens_123456")
from fastapi.testclient import TestClient

# Add backend to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from app import create_app
from core.authentication import create_access_token, get_password_hash
from models.database import SessionLocal
from models.models import User

@pytest.fixture(scope="session")
def app():
    return create_app()

@pytest.fixture(scope="session")
def client(app):
    return TestClient(app)

@pytest.fixture(scope="session")
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="session")
def test_user(db_session):
    email = "test@example.com"
    user = db_session.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            hashed_password=get_password_hash("testpassword"),
            profile_json={"name": "Test User"},
            onboarding_status="COMPLETE"
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
    return user

@pytest.fixture(scope="session")
def auth_headers(test_user):
    # Check if we are running integration tests against a live URL
    base_url = os.environ.get("TEST_BASE_URL")
    if base_url:
        import requests
        # Try to login
        login_url = f"{base_url}/api/auth/login"
        # Since test_user fixture ensures the user exists with this password
        payload = {"username": "test@example.com", "password": "testpassword"}
        try:
            print(f"DEBUG: Attempting login to {login_url}")
            response = requests.post(login_url, json=payload, timeout=5)
            if response.status_code == 200:
                token = response.json().get("access_token")
                print("DEBUG: Login successful, got token.")
                return {"Authorization": f"Bearer {token}"}
            else:
                 print(f"WARNING: Login failed with {response.status_code}: {response.text}")
        except Exception as e:
            print(f"WARNING: Could not connect to {login_url}: {e}")

    # Fallback to local minting (UNIT TEST MODE or if login failed)
    print("DEBUG: Minting local token")
    access_token = create_access_token({"sub": test_user.email})
    return {"Authorization": f"Bearer {access_token}"}
