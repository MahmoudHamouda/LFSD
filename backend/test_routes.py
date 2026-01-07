"""
Test backend API routes directly
"""

import requests
import json
import sys

BACKEND_URL = "https://lfsd-backend-wpvii577oq-ww.a.run.app"

# Login
print("=" * 80)
print("TESTING BACKEND ROUTES DIRECTLY")
print("=" * 80)

print("\n1. Logging in as finance@helm.com...")
login_response = requests.post(
    f"{BACKEND_URL}/api/auth/login",
    json={"username": "finance@helm.com", "password": "P@ssword123"},
    headers={"Content-Type": "application/json"}
)

if login_response.status_code != 200:
    print(f"✗ Login failed: {login_response.status_code}")
    print(login_response.text)
    sys.exit(1)

token = login_response.json().get("access_token")
headers = {"Authorization": f"Bearer {token}"}
print("✓ Login successful")

# Test Routes
routes_to_test = [
    "/api/finance/transactions",
    "/api/financial/transactions",
    "/api/finance/accounts",
    "/api/financial/accounts",
    "/api/scores/current",
    "/api/finance/scores/current"
]

print("\n2. Testing Endpoint Existence...")
for route in routes_to_test:
    url = f"{BACKEND_URL}{route}"
    print(f"\n   Checking: {url}")
    try:
        response = requests.get(url, headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            # print snippet
            snippet = json.dumps(data)[:100]
            print(f"   Response: {snippet}...")
        else:
            print(f"   Error: {response.text[:100]}")
    except Exception as e:
        print(f"   Exception: {e}")

print("\n" + "=" * 80)
