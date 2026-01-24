
import requests
import sys
import json

# Force output flushing
sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "https://lfsd-backend-692544481281.us-central1.run.app"

def run():
    print("--- STARTING REMOTE CALCULATION TRIGGER ---", flush=True)
    
    # Login
    token_url = f"{BASE_URL}/api/user/token"
    payload = {"username": "finance@helm.com", "password": "P@ssword123"}
    
    token = None
    try:
        print(f"Logging in to {token_url}...", flush=True)
        resp = requests.post(token_url, data=payload, timeout=15)
        if resp.status_code != 200:
            print(f"LOGIN FAILED: {resp.status_code}\n{resp.text}", flush=True)
            return
            
        token = resp.json().get("access_token")
        print(f"Login OK.", flush=True)
        
    except Exception as e:
        print(f"LOGIN EXCEPTION: {e}", flush=True)
        return

    # Trigger Calc
    url = f"{BASE_URL}/api/scores/debug/trigger_calc"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        print(f"Requesting POST {url}...", flush=True)
        resp = requests.post(url, headers=headers, timeout=60)
        
        print(f"SC_STATUS: {resp.status_code}", flush=True)
        print("RESPONSE:", flush=True)
        print(resp.text, flush=True)
        
    except Exception as e:
        print(f"REQUEST EXCEPTION: {e}", flush=True)

if __name__ == "__main__":
    run()
