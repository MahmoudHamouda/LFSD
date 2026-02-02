"""
Quick script to check if data exists for the logged-in user
"""
import requests

# The user ID from /api/auth/me
USER_ID = "f95ddf3d-30a9-4aef-8384-d3ed0aaec8dc"
BACKEND_URL = "https://lfsd-backend-692544481281.us-central1.run.app"

print(f"Checking data for user: {USER_ID}")
print("=" * 60)

# Check VivIndex
response = requests.get(f"{BACKEND_URL}/api/scores/viv/{USER_ID}")
print(f"\nVivIndex endpoint: {response.status_code}")
if response.status_code == 200:
    print(response.json())
else:
    print(f"Error: {response.text}")

# Check Financial Summary
response = requests.get(f"{BACKEND_URL}/api/finance/summary?user_id={USER_ID}")
print(f"\nFinance Summary endpoint: {response.status_code}")
if response.status_code == 200:
    print(response.json())
else:
    print(f"Error: {response.text}")
