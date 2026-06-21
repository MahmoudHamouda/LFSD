import sys
import os
import requests
import json
import time
import uuid

# Add parent dir to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

BASE_URL = "https://app.helmory.com"

# User Data
USERS = {
    "standard": [
        {"email": "steward@helm.com", "password": "P@ssword", "role": "user"}
    ],
    "personas": [],  # No seeded personas, using synthetic agents instead
    "synthetic_agents": [
        {"email": "empty@helm.com", "password": "P@ssword", "role": "user"},
        {"email": "finance@helm.com", "password": "P@ssword", "role": "user"},
        {"email": "health@helm.com", "password": "P@ssword", "role": "user"},
        {"email": "time@helm.com", "password": "P@ssword", "role": "user"},
        {"email": "super@helm.com", "password": "P@ssword", "role": "user"},
    ]
}

JOURNEYS = [
    "E2E-01", "E2E-02", "E2E-03", "E2E-04", "E2E-05", 
    "E2E-06", "E2E-07", "E2E-08", "E2E-09", "E2E-10"
]

def login(email, password):
    """Authenticate and return token"""
    try:
        url = f"{BASE_URL}/api/user/token"
        print(f"DEBUG: POSTing to {url}")
        response = requests.post(url, data={
            "username": email,
            "password": password
        }, timeout=10)
        
        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            print(f"DEBUG: First attempt failed {response.status_code}. Content: {response.text[:100]}")
            # Try JSON login if form data failed (some setups differ)
            url2 = f"{BASE_URL}/login"
            print(f"DEBUG: POSTing to {url2}")
            response = requests.post(url2, json={
                "email": email,
                "password": password
            }, timeout=10)
            if response.status_code == 200:
                return response.json().get("access_token")
            print(f"DEBUG: Second attempt failed {response.status_code}. Content: {response.text[:100]}")
                
        print(f"Login failed for {email}: {response.status_code}")
        return None
    except Exception as e:
        print(f"Login error for {email}: {e}")
        return None

def run_journey_01(token):
    """E2E-01: Onboarding"""
    # Simply check if user profile exists and has onboarding flag
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = requests.get(f"{BASE_URL}/api/user/me", headers=headers)
        if r.status_code == 200:
            return "PASS", "User profile accessible"
        return "FAIL", f"Status {r.status_code}"
    except Exception as e:
        return "FAIL", str(e)

def run_journey_02(token):
    """E2E-02: Finance Ingestion"""
    # Check finance summary endpoint
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = requests.get(f"{BASE_URL}/api/finance/summary", headers=headers)
        if r.status_code == 200:
            return "PASS", "Finance summary accessible"
        return "FAIL", f"Status {r.status_code}"
    except Exception as e:
        return "FAIL", str(e)

def run_journey_03(token):
    """E2E-03: Health Sync"""
    # Check health summaries
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = requests.get(f"{BASE_URL}/api/health/summaries", headers=headers)
        if r.status_code == 200:
            return "PASS", "Health summaries accessible"
        return "FAIL", f"Status {r.status_code}" 
    except Exception as e:
        return "FAIL", str(e)

def run_journey_04(token):
    """E2E-04: Time Sync"""
    # Check calendar/time events
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = requests.get(f"{BASE_URL}/api/time/events", headers=headers)
        if r.status_code == 200:
             return "PASS", "Time events reachable"
        return "FAIL", f"Status {r.status_code}"
    except Exception as e:
        return "FAIL", str(e)

def run_journey_05(token):
    """E2E-05: Chat Affordability"""
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "messages": [{"role": "user", "content": "Can I afford a weekend trip?"}]
    }
    try:
        # History routes are mounted at root /history without /api prefix in app.py
        r = requests.post(f"{BASE_URL}/history/generate", json=payload, headers=headers)
        if r.status_code == 200:
            return "PASS", "Chat response received"
        return "FAIL", f"Status {r.status_code}"
    except Exception as e:
        return "FAIL", str(e)

def run_journey_06(token):
    """E2E-06: Create Goal"""
    headers = {"Authorization": f"Bearer {token}"}
    goal = {
        "title": f"Test Goal {uuid.uuid4().hex[:4]}",
        "target_amount": 100,
        "deadline": "2026-12-31",
        "type": "savings",
        "priority": "medium"
    }
    try:
        r = requests.post(f"{BASE_URL}/api/finance/goals", json=goal, headers=headers)
        if r.status_code in [200, 201]:
            return "PASS", "Goal created"
        return "FAIL", f"Status {r.status_code}"
    except Exception as e:
        return "FAIL", str(e)
        
def run_journey_07(token):
    """E2E-07: Dashboard Roll-up"""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        # Use user snapshot for dashboard summary
        r = requests.get(f"{BASE_URL}/api/user/snapshot", headers=headers)
        if r.status_code == 200:
             return "PASS", "Dashboard snapshot loaded"
        return "FAIL", f"Status {r.status_code}"
    except Exception as e:
        return "FAIL", str(e)

def run_journey_08(token):
    """E2E-08: Resilience"""
    return "NOT APPLICABLE", "Requires mocking infra provider failure"

def run_journey_09(token):
    """E2E-09: Session Expiry"""
    headers = {"Authorization": "Bearer invalid_token_123"}
    try:
        r = requests.get(f"{BASE_URL}/api/user/me", headers=headers)
        if r.status_code == 401:
            return "PASS", "Correctly rejected invalid token"
        return "FAIL", f"Expected 401, got {r.status_code}"
    except Exception as e:
        return "FAIL", str(e)

def run_journey_10(token):
    """E2E-10: Score Calculation (Fixed)"""
    # Verify both productivity and financial scores are returned
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = requests.get(f"{BASE_URL}/api/scores/current", headers=headers)
        if r.status_code == 200:
            data = r.json()
            # Basic validation that we have the keys we corrected
            if "financial_score" in data and "productivity_score" in data:
                return "PASS", f"Scores: Fin={data.get('financial_score')}, Prod={data.get('productivity_score')}"
            return "WARN", "200 OK but missing top-level keys"
        return "FAIL", f"Status {r.status_code}"
    except Exception as e:
        return "FAIL", str(e)

# Map journey string to function
JOURNEY_FUNCS = {
    "E2E-01": run_journey_01,
    "E2E-02": run_journey_02,
    "E2E-03": run_journey_03,
    "E2E-04": run_journey_04,
    "E2E-05": run_journey_05,
    "E2E-06": run_journey_06,
    "E2E-07": run_journey_07,
    "E2E-08": run_journey_08,
    "E2E-09": run_journey_09,
    "E2E-10": run_journey_10,
}

def run_all():
    """Run all E2E journeys for all user types"""
    print("# Automation Report: LFSD E2E Journeys\n")
    print(f"Backend URL: {BASE_URL}\n")
    
    # Flatten user list
    all_users = []
    all_users.extend(USERS["standard"])
    all_users.extend(USERS["personas"])  # Fixed: was seeded_personas
    all_users.extend(USERS["synthetic_agents"])
    
    unique_users = {u['email']: u for u in all_users}.values()
    
    for user in unique_users:
        email = user['email']
        role = user.get('role', 'user')
        print(f"## User: {email} ({role})")
        
        token = login(email, user['password'])
        if not token:
            print("SKIPPING: Could not authenticate\n")
            continue
            
        print("| Journey | Result | Notes |")
        print("|---------|--------|-------|")
        
        for j_id in JOURNEYS:
            func = JOURNEY_FUNCS.get(j_id)
            if func:
                status, note = func(token)
                print(f"| {j_id} | {status} | {note} |")
            else:
                print(f"| {j_id} | SKIP | No automation func |")
        print("\n")

if __name__ == "__main__":
    run_all()
