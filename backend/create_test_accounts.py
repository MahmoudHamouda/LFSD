"""
Create test accounts via the signup API endpoint
This ensures password hashes are created using the backend's method
"""

import requests
import json

BACKEND_URL = "https://lfsd-backend-wpvii577oq-ww.a.run.app"
PASSWORD = "P@ssword123"

accounts = [
    {"email": "empty@helm.com", "name": "Empty User"},
    {"email": "finance@helm.com", "name": "Finance User"},
    {"email": "health@helm.com", "name": "Health User"},
    {"email": "time@helm.com", "name": "Time User"},
    {"email": "super@helm.com", "name": "Super User"},
]

print("Creating test accounts...")
print("=" * 80)

for account in accounts:
    print(f"\nCreating: {account['email']}")
    
    try:
        # Call signup API
        response = requests.post(
            f"{BACKEND_URL}/api/auth/signup",
            json={
                "email": account["email"],
                "password": PASSWORD,
                "name": account["name"]
            },
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200 or response.status_code == 201:
            data = response.json()
            print(f"✓ Created: {data.get('email')} (ID: {data.get('user_id')})")
        elif response.status_code == 409:
            print(f"⚠ Account already exists: {account['email']}")
        else:
            print(f"✗ Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"✗ Exception: {e}")

print("\n" + "=" * 80)
print(f"✓ Account creation complete!")
print(f"Password for all accounts: {PASSWORD}")
