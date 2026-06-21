from fastapi.testclient import TestClient
from backend.app import create_app
import pytest

app = create_app()
client = TestClient(app)


def test_router_integrity():
    """
    Verify that there are no duplicate routes registered.
    """
    start_routes = [route for route in app.routes]

    unique_routes = set()
    duplicates = []

    for route in start_routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            # Create a unique signature for each route: (path, sorted(methods))
            methods = tuple(sorted(list(route.methods)))
            signature = (route.path, methods)

            if signature in unique_routes:
                duplicates.append(signature)
            else:
                unique_routes.add(signature)

    if duplicates:
        pytest.fail(f"Duplicate routes found: {duplicates}")


def test_essential_endpoints_reachable():
    """
    Verify that key endpoints return expected status codes (not 404).
    """
    # Test Public Health Check (if exists) or Docs
    response = client.get("/docs")
    assert response.status_code == 200

    # Test Auth Endpoint (should be 405 Method Not Allowed for GET, or 422 for POST w/o body, but NOT 404)
    response = client.post("/api/auth/signup", json={})
    assert response.status_code == 422  # Validation Error means it found the route

    # Test Onboarding Endpoint (POST to upload-whoop)
    response = client.post("/api/onboarding/upload-whoop", json={"files": []})
    # Should be 200 or 422, but definitely not 404
    assert response.status_code != 404
