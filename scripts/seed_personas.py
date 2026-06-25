import requests
import datetime
import random
import time
import uuid

# Configuration
BACKEND_URL = "https://lfsd-backend-692544481281.us-central1.run.app"
AUTH0_DOMAIN = "dev-lmc05ou12e7ep05p.eu.auth0.com"
AUTH0_MGMT_CLIENT_ID = "IRJU5sZi2elmPMgqyC3cvYVSQvzFUzia"
AUTH0_MGMT_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET", "dummy_secret")

PERSONAS = [
    {"email": "finance.v6@helm.com", "password": "P@ssword123", "name": "Finance User", "type": "finance"},
    {"email": "health.v6@helm.com", "password": "P@ssword123", "name": "Health User", "type": "health"},
    {"email": "time.v6@helm.com", "password": "P@ssword123", "name": "Time User", "type": "time"},
    {"email": "super.v6@helm.com", "password": "P@ssword123", "name": "Super User", "type": "super"}
]

def get_mgmt_token():
    print(f"Getting Management API token for {AUTH0_DOMAIN}...")
    url = f"https://{AUTH0_DOMAIN}/oauth/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": AUTH0_MGMT_CLIENT_ID,
        "client_secret": AUTH0_MGMT_CLIENT_SECRET,
        "audience": f"https://{AUTH0_DOMAIN}/api/v2/"
    }
    response = requests.post(url, json=payload)
    response.raise_for_status()
    print("✓ Management token obtained.")
    return response.json()["access_token"]

def ensure_auth0_user(email, password, name, mgmt_token):
    print(f"  Ensuring Auth0 user exists: {email}")
    url = f"https://{AUTH0_DOMAIN}/api/v2/users"
    headers = {"Authorization": f"Bearer {mgmt_token}"}
    
    # Check if user exists first
    search_url = f"https://{AUTH0_DOMAIN}/api/v2/users-by-email?email={email}"
    search_resp = requests.get(search_url, headers=headers)
    if search_resp.status_code == 200 and search_resp.json():
        print(f"  ✓ User already exists in Auth0.")
        return search_resp.json()[0]

    # Create user
    payload = {
        "email": email,
        "password": password,
        "name": name,
        "connection": "Username-Password-Authentication",
        "email_verified": True,
        "verify_email": False
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 201:
        print(f"  ✓ User created in Auth0.")
        return response.json()
    else:
        print(f"  ✗ Failed to create user: {response.text}")
        response.raise_for_status()

def get_user_token(email, password):
    """
    Attempt to get a user token via Resource Owner Password Grant.
    Note: This requires 'Password' grant enabled in Auth0 for the client.
    """
    print(f"  Getting user token for {email}...")
    url = f"https://{AUTH0_DOMAIN}/oauth/token"
    payload = {
        "grant_type": "password",
        "username": email,
        "password": password,
        "client_id": AUTH0_MGMT_CLIENT_ID,
        "client_secret": AUTH0_MGMT_CLIENT_SECRET,
        "audience": f"https://{AUTH0_DOMAIN}/api/v2/",
        "scope": "openid profile email"
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("  ✓ User token obtained.")
        return response.json()["id_token"] if "id_token" in response.json() else response.json()["access_token"]
    else:
        print(f"  ✗ Failed to get user token (ROPG might be disabled): {response.text}")
        return None

def seed_finance(token, user_id=None):
    print("  Seeding 6 months of financial transactions...")
    headers = {"Authorization": f"Bearer {token}"}
    if user_id:
        headers["X-Test-User-Id"] = user_id
        
    today = datetime.datetime.now()
    count = 0
    
    for month in range(6):
        month_date = today - datetime.timedelta(days=month*30)
        
        # Salary
        for week in range(2):
            date_str = (month_date - datetime.timedelta(days=week*14)).strftime("%Y-%m-%d")
            payload = {"amount": 2500.0, "category": "income", "description": "Salary", "date": date_str}
            requests.post(f"{BACKEND_URL}/api/finance/transactions", json=payload, headers=headers)
            count += 1
            
        # Rent
        payload = {"amount": -2000.0, "category": "housing", "description": "Rent", "date": month_date.strftime("%Y-%m-%d")}
        requests.post(f"{BACKEND_URL}/api/finance/transactions", json=payload, headers=headers)
        count += 1
        
        # Daily expenses
        for day in range(15):  # Fewer days to speed up seeding
            date_str = (month_date - datetime.timedelta(days=day*2)).strftime("%Y-%m-%d")
            amount = -round(random.uniform(5, 50), 2)
            category = random.choice(["food", "transport", "entertainment", "health"])
            payload = {"amount": amount, "category": category, "description": "Expense", "date": date_str}
            requests.post(f"{BACKEND_URL}/api/finance/transactions", json=payload, headers=headers)
            count += 1
            
    print(f"  ✓ Seeded {count} transactions.")

def seed_health(token, user_id=None):
    print("  Seeding 30 days of health data...")
    headers = {"Authorization": f"Bearer {token}"}
    if user_id:
        headers["X-Test-User-Id"] = user_id
        
    today = datetime.datetime.now()
    count = 0
    
    for day in range(30):
        date_str = (today - datetime.timedelta(days=day)).strftime("%Y-%m-%d")
        payload = {
            "date": date_str,
            "steps": random.randint(5000, 15000),
            "calories": random.randint(1800, 2500),
            "sleep_hours": round(random.uniform(6.0, 9.0), 1)
        }
        requests.post(f"{BACKEND_URL}/api/health/daily-summary", json=payload, headers=headers)
        count += 1
    print(f"  ✓ Seeded {count} health entries.")

def seed_time(token, user_id=None):
    print("  Seeding 30 days of calendar events...")
    headers = {"Authorization": f"Bearer {token}"}
    if user_id:
        headers["X-Test-User-Id"] = user_id
        
    today = datetime.datetime.now()
    count = 0
    
    for day in range(30):
        date = today - datetime.timedelta(days=day)
        if date.weekday() < 5:  # Weekdays
            # Meeting
            start = date.replace(hour=9, minute=0, second=0).strftime("%Y-%m-%dT%H:%M:%S")
            end = date.replace(hour=9, minute=30, second=0).strftime("%Y-%m-%dT%H:%M:%S")
            payload = {"title": "Daily Sync", "start_time": start, "end_time": end, "category": "meeting"}
            requests.post(f"{BACKEND_URL}/api/calendar/events", json=payload, headers=headers)
            count += 1
            
            # Focused work
            start = date.replace(hour=14, minute=0, second=0).strftime("%Y-%m-%dT%H:%M:%S")
            end = date.replace(hour=16, minute=0, second=0).strftime("%Y-%m-%dT%H:%M:%S")
            payload = {"title": "Deep Work", "start_time": start, "end_time": end, "category": "work"}
            requests.post(f"{BACKEND_URL}/api/calendar/events", json=payload, headers=headers)
            count += 1
            
    print(f"  ✓ Seeded {count} events.")

def main():
    print("=== LFSD Seeding Tool (Python) ===")
    mgmt_token = get_mgmt_token()
    
    for persona in PERSONAS:
        print(f"\nProcessing {persona['name']}...")
        auth0_user = ensure_auth0_user(persona["email"], persona["password"], persona["name"], mgmt_token)
        
        # We need to hit a "protected" endpoint with a valid Auth0 token at least once
        # to ensure the user is auto-created in the backend's ephemeral DB.
        # If ROPG is disabled, we might have to use the X-Test-User-Id bypass
        # but that bypass only works if the user is ALREADY in the DB.
        # Chicken and egg! 
        
        token = get_user_token(persona["email"], persona["password"])
        
        # If we got a token, we can seed normally.
        # If not, we'll try to use the Management ID and email in a dummy request
        # But wait, our backend's bypass uses email/id to find user. 
        # If the user doesn't exist, the bypass fails.
        
        if not token:
            print("  ! Could not get user token. Assuming seeding needs manual login or ROPG activation.")
            print("  ! Skipping data seeding for this persona until ROPG is enabled or user logs in once.")
            continue
            
        if persona["type"] == "finance" or persona["type"] == "super":
            seed_finance(token)
        if persona["type"] == "health" or persona["type"] == "super":
            seed_health(token)
        if persona["type"] == "time" or persona["type"] == "super":
            seed_time(token)

    print("\nSeeding completed.")

if __name__ == "__main__":
    main()
