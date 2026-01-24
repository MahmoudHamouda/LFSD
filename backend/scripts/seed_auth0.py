import requests
import time

AUTH0_DOMAIN = "dev-lmc05ou12e7ep05p.eu.auth0.com"
CLIENT_ID = "VVw94DZQITVcARsNlp4JEZkyzMjsgioF"
CONNECTION = "Username-Password-Authentication"
PASSWORD = "P@ssword123"

# Users to create
users = [
    "empty@helm.com",
    "finance@helm.com",
    "health@helm.com",
    "time@helm.com",
    "super@helm.com"
]

url = f"https://{AUTH0_DOMAIN}/dbconnections/signup"

print("--- Seeding Auth0 Users ---")
for email in users:
    print(f"Processing {email}...")
    payload = {
        "client_id": CLIENT_ID,
        "email": email,
        "password": PASSWORD,
        "connection": CONNECTION
    }
    
    try:
        resp = requests.post(url, json=payload)
        
        if resp.status_code == 200 or resp.status_code == 201:
            print(f"✅ Success: Created {email}")
        else:
            # Check for specific error messages
            try:
                data = resp.json()
                if data.get("code") == "user_exists" or "user already exists" in str(data):
                    print(f"⚠️  Skipped: {email} already exists")
                else:
                    print(f"❌ Failed: {email} - {data}")
            except:
                print(f"❌ Failed: {email} - Status: {resp.status_code}")
                
    except Exception as e:
        print(f"❌ Error connecting for {email}: {str(e)}")
        
    time.sleep(1) # Avoid rate limits

print("\n--- Seeding Complete ---")
