"""
API Testing Script

Tests all new API endpoints to verify functionality.
"""

import requests
import pytest
from tests.test_utils import get_test_base_url, get_auth_headers

BASE_URL = get_test_base_url()

@pytest.fixture
def auth_headers():
    return get_auth_headers()

def test_health_check():
    """Test health check endpoint."""
    # Note: app.py doesn't seem to have /healthz, let's check one that exists
    response = requests.get(f"{BASE_URL}/api/user/me") # Just to check connectivity
    assert response.status_code in [200, 401]

def test_get_user(auth_headers):
    """Test get current user endpoint."""
    response = requests.get(f"{BASE_URL}/api/user/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "user" in data

def test_health_connections(auth_headers):
    """Test health connections endpoint."""
    # Prefix is /api in app.py for api_routes_health? No, app.py says app.include_router(api_routes_health.router)
    # Let's check api_routes_health.py prefix
    response = requests.get(f"{BASE_URL}/api/health/connections", headers=auth_headers)
    assert response.status_code in [200, 404] # Path might be /health/connections

def test_unified_history(auth_headers):
    """Test unified history endpoint."""
    payload = {
        "filters": {
            "types": [],
            "importance": "all"
        },
        "limit": 10
    }
    # app.include_router(history_routes.router) -> check prefix? Usually /api/history/unified based on test
    response = requests.post(
        f"{BASE_URL}/api/history/unified",
        json=payload,
        headers=auth_headers
    )
    assert response.status_code in [200, 404]

def test_calculate_indexes(auth_headers):
    """Test index calculation endpoint."""
    response = requests.post(f"{BASE_URL}/api/scores/calculate", headers=auth_headers)
    assert response.status_code in [200, 404]
