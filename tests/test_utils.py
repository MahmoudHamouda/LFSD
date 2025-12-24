import os
import sys

# Add backend to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from core.authentication import create_access_token

def get_auth_headers(email="test@example.com"):
    token = create_access_token({"sub": email})
    return {"Authorization": f"Bearer {token}"}

def get_test_base_url():
    return os.getenv("TEST_BASE_URL", "http://localhost:8003")
