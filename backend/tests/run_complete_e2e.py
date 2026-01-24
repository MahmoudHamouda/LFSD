import requests
import time
import sys

URL = "https://lfsd-backend-692544481281.us-central1.run.app"

print("="*70)
print("AUTONOMOUS E2E TESTING - COMPLETE WORKFLOW")
print("="*70)

# PHASE 1: Wait for deployment
print("\n[PHASE 1] Waiting for deployment...")
for attempt in range(1, 11):
    print(f"  Attempt {attempt}/10 - Checking deployment status...")
    try:
        response = requests.post(f"{URL}/api/debug/seed_force", params={"secret": "lfsd_backup_2024"}, timeout=10)
        result = response.json()
        
        if 'user_seed_status' in result:
            print(f"  ✅ NEW CODE DEPLOYED!")
            print(f"     User Seed Status: {result.get('user_seed_status')}")
            
            if result.get('user_seed_status') == 'SUCCESS':
                print(f"  🎉 USERS SEEDED SUCCESSFULLY!")
                break
            elif result.get('user_seed_status') == 'FAILED':
                print(f"  ❌ Seeding failed: {result.get('message')}")
                sys.exit(1)
        else:
            print(f"  ⏳ Old code still running...")
    except Exception as e:
        print(f"  ⚠️ Error: {e}")
    
    if attempt < 10:
        print(f"  Waiting 20 seconds...")
        time.sleep(20)
else:
    print("\n❌ Deployment timeout after 10 attempts (200 seconds)")
    print("Manual intervention required.")
    sys.exit(1)

# PHASE 2: Verify logins
print("\n[PHASE 2] Verifying user logins...")
test_users = [
    ("david@example.com", "password"),
    ("sara@example.com", "password"),
    ("alex@example.com", "password"),
    ("finance@helm.com", "P@ssword123"),
    ("empty@helm.com", "P@ssword123"),
    ("health@helm.com", "P@ssword123"),
    ("time@helm.com", "P@ssword123"),
    ("super@helm.com", "P@ssword123"),
]

login_passed = 0
login_failed = 0

for email, password in test_users:
    try:
        response = requests.post(f"{URL}/api/user/token", data={"username": email, "password": password}, timeout=5)
        if response.status_code == 200:
            print(f"  ✅ {email}")
            login_passed += 1
        else:
            print(f"  ❌ {email} - {response.status_code}")
            login_failed += 1
    except Exception as e:
        print(f"  ❌ {email} - Error: {e}")
        login_failed += 1

print(f"\nLogin Results: {login_passed} passed, {login_failed} failed")

if login_failed > 0:
    print("❌ Some logins failed. Cannot proceed with E2E tests.")
    sys.exit(1)

print("✅ All login verifications passed!")

# PHASE 3: Run E2E Tests
print("\n[PHASE 3] Running E2E Test Suite...")
print("-"*70)

import subprocess
result = subprocess.run(
    ["python", "tests/e2e/run_journeys.py"],
    capture_output=True,
    text=True,
    cwd="."
)

print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)

# PHASE 4: Summary
print("\n" + "="*70)
print("E2E TESTING COMPLETE")
print("="*70)
print(f"Deployment: ✅ SUCCESS")
print(f"Logins: ✅ {login_passed}/{len(test_users)} passed")
print(f"E2E Tests: {'✅ SUCCESS' if result.returncode == 0 else '❌ FAILURES DETECTED'}")
print("="*70)

sys.exit(result.returncode)
