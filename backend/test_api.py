"""
Test backend API to check if data is being returned
"""

import requests
import json

BACKEND_URL = "https://lfsd-backend-wpvii577oq-ww.a.run.app"

# First, login to get a token
print("=" * 80)
print("TESTING BACKEND API")
print("=" * 80)

print("\n1. Logging in as finance@helm.com...")
login_response = requests.post(
    f"{BACKEND_URL}/api/auth/login",
    json={"username": "finance@helm.com", "password": "P@ssword123"},
    headers={"Content-Type": "application/json"}
)

if login_response.status_code == 200:
    data = login_response.json()
    token = data.get("access_token")
    user = data.get("user", {})
    print(f"✓ Login successful!")
    print(f"  User ID: {user.get('id')}")
    print(f"  Email: {user.get('email')}")
    print(f"  Name: {user.get('name')}")
    
    # Test getting scores
    print("\n2. Fetching VivIndex scores...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to get the user's data
    endpoints_to_test = [
        "/api/user/index",
        "/api/finance/summary",
        "/api/health/summary",
        "/frontend_settings"
    ]
    
    for endpoint in endpoints_to_test:
        print(f"\n   Testing: {endpoint}")
        try:
            response = requests.get(f"{BACKEND_URL}{endpoint}", headers=headers)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                json_data = response.json()
                print(f"   Response: {json.dumps(json_data, indent=2)[:500]}...")
            else:
                print(f"   Error: {response.text[:200]}")
        except Exception as e:
            print(f"   Exception: {e}")
            
else:
    print(f"✗ Login failed: {login_response.status_code}")
    print(f"  Response: {login_response.text}")

print("\n" + "=" * 80)
