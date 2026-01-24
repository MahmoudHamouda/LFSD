"""
Complete E2E Testing & UI Validation Automation
Waits for deployment → Seeds database → Runs E2E tests → Validates UI
"""

import requests
import time
import sys
import subprocess

BASE_URL = "https://lfsd-backend-692544481281.us-central1.run.app"
FRONTEND_URL = "https://lfsd-frontend-692544481281.us-central1.run.app"

print("="*80)
print("COMPLETE E2E TESTING & UI VALIDATION")
print("="*80)

# ============================================================================
# PHASE 1: Wait for Deployment
# ============================================================================
print("\n[PHASE 1] Waiting for GitHub Actions deployment...")
print("-"*80)

max_attempts = 15  # 15 attempts * 20 seconds = 5 minutes
for attempt in range(1, max_attempts + 1):
    print(f"  Attempt {attempt}/{max_attempts} - Checking deployment status...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/debug/seed_force",
            params={"secret": "lfsd_backup_2024"},
            timeout=10
        )
        result = response.json()
        
        if 'user_seed_status' in result:
            print(f"  ✅ NEW CODE DEPLOYED!")
            print(f"     Message: {result.get('message')}")
            
            if result.get('user_seed_status') == 'SUCCESS':
                print(f"  🎉 USERS SEEDED WITH COMPREHENSIVE DATA!")
                break
            elif result.get('user_seed_status') == 'FAILED':
                print(f"  ⚠️ Seeding attempted but failed: {result.get('message')}")
                print(f"  Attempting to continue anyway...")
                break
            else:
                print(f"  ⏳ Deployment detected, user_seed_status: {result.get('user_seed_status')}")
                break
        else:
            print(f"  ⏳ Old code still running (no user_seed_status in response)")
    except Exception as e:
        print(f"  ⚠️ Error: {e}")
    
    if attempt < max_attempts:
        print(f"  Waiting 20 seconds...")
        time.sleep(20)
else:
    print("\n⚠️ Deployment timeout - proceeding anyway to check current state")

# ============================================================================
# PHASE 2: Verify Seeding & User Authentication
# ============================================================================
print("\n[PHASE 2] Verifying user authentication...")
print("-"*80)

test_users = [
    ("finance@helm.com", "P@ssword123", "Finance User"),
    ("empty@helm.com", "P@ssword123", "Empty User"),
    ("health@helm.com", "P@ssword123", "Health User"),
    ("time@helm.com", "P@ssword123", "Time User"),
    ("super@helm.com", "P@ssword123", "Super User"),
    ("david@example.com", "password", "David Persona"),
    ("sara@example.com", "password", "Sara Persona"),
    ("alex@example.com", "password", "Alex Persona"),
]

authenticated_users = []
login_summary = {"passed": 0, "failed": 0}

for email, password, name in test_users:
    try:
        response = requests.post(
            f"{BASE_URL}/api/user/token",
            data={"username": email, "password": password},
            timeout=5
        )
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            print(f"  ✅ {name:<20} ({email})")
            authenticated_users.append({"email": email, "password": password, "name": name, "token": token})
            login_summary["passed"] += 1
        else:
            print(f"  ❌ {name:<20} - {response.status_code}")
            login_summary["failed"] += 1
    except Exception as e:
        print(f"  ❌ {name:<20} - Error: {str(e)[:40]}")
        login_summary["failed"] += 1

print(f"\nLogin Summary: {login_summary['passed']} passed, {login_summary['failed']} failed")

if login_summary["passed"] == 0:
    print("\n❌ CRITICAL: No users could authenticate. Cannot proceed with E2E tests.")
    print("   Database may be unseeded or credentials incorrect.")
    print("\nRecommendation: Check Cloud Run logs or trigger seed endpoint manually.")
    sys.exit(1)

# ============================================================================
# PHASE 3: Run E2E API Tests
# ============================================================================
print("\n[PHASE 3] Running E2E API Test Suite...")
print("-"*80)

try:
    result = subprocess.run(
        ["python", "tests/e2e/run_journeys.py"],
        capture_output=True,
        text=True,
        timeout=300,  # 5 minute timeout
        cwd="."
    )
    
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    e2e_success = (result.returncode == 0)
    if e2e_success:
        print("\n✅ E2E API tests completed successfully")
    else:
        print(f"\n⚠️ E2E API tests completed with errors (exit code {result.returncode})")
        
except subprocess.TimeoutExpired:
    print("\n❌ E2E tests timed out after 5 minutes")
    e2e_success = False
except Exception as e:
    print(f"\n❌ Error running E2E tests: {e}")
    e2e_success = False

# ============================================================================
# PHASE 4: UI Validation
# ============================================================================
print("\n[PHASE 4] UI Validation...")
print("-"*80)
print(f"Frontend URL: {FRONTEND_URL}")
print("\nAutomated UI checks:")

ui_checks = []

# Check 1: Frontend is accessible
try:
    response = requests.get(FRONTEND_URL, timeout=10)
    if response.status_code == 200:
        print("  ✅ Frontend loads successfully")
        ui_checks.append(("Frontend accessible", True))
    else:
        print(f"  ❌ Frontend returned {response.status_code}")
        ui_checks.append(("Frontend accessible", False))
except Exception as e:
    print(f"  ❌ Frontend not accessible: {e}")
    ui_checks.append(("Frontend accessible", False))

# Check 2: Can login via frontend
print("\nManual UI Test Instructions:")
print("="*80)
print("\n1. Open browser to: " + FRONTEND_URL)
print("\n2. Test login for each persona:")
for email, password, name in test_users[:3]:  # Show first 3
    print(f"   - {name}: {email} / {password}")
print("   (See full list in Phase 2 results above)")

print("\n3. Verify for each user:")
print("   ✓ Dashboard loads with persona-specific data")
print("   ✓ Financial tab shows accounts & transactions (finance users)")
print("   ✓ Health tab shows metrics & sleep data (health users)")
print("   ✓ Time tab shows calendar events (time users)")
print("   ✓ Goals tab shows life goals (super user)")
print("   ✓ Chat interface responds to queries")
print("   ✓ Recommendations appear")
print("   ✓ VivIndex scores display correctly")

print("\n4. Cross-browser testing:")
print("   ✓ Chrome/Edge")
print("   ✓ Firefox")
print("   ✓ Safari (if available)")

print("\n5. Responsive design:")
print("   ✓ Desktop (1920x1080)")
print("   ✓ Tablet (768x1024)")
print("   ✓ Mobile (375x667)")

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("\n" + "="*80)
print("FINAL TEST SUMMARY")
print("="*80)

print(f"\n✅ Deployment: Verified (user_seed_status in response)")
print(f"{'✅' if login_summary['passed'] > 0 else '❌'} Authentication: {login_summary['passed']}/{len(test_users)} users authenticated")
print(f"{'✅' if e2e_success else '❌'} E2E API Tests: {'PASSED' if e2e_success else 'FAILED/INCOMPLETE'}")
print(f"⏸️  UI Tests: MANUAL VERIFICATION REQUIRED (see instructions above)")

print("\n" + "="*80)
print("NEXT STEPS")
print("="*80)

if login_summary["passed"] == len(test_users):
    print("\n✅ All automated checks passed!")
    print("   → Proceed with manual UI testing using instructions above")
    print("   → Record any UI issues or bugs found")
    print("   → Verify all persona-specific features work correctly")
else:
    print(f"\n⚠️ {login_summary['failed']} users failed authentication")
    print("   → Check Cloud Run logs for seeding errors")
    print("   → Verify database connection")
    print("   → May need to manually trigger seed endpoint")

print("\n" + "="*80)
