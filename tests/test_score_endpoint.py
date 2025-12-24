import requests
import json

url = "http://127.0.0.1:8000/api/scores/onboarding"
# Note: User env says port 8005 sometimes? Frontend vite config proxy says 8005. 
# But usually uvicorn default is 8000. 
# check `vite.config.ts`: target: 'http://127.0.0.1:8005'
# So I should try 8005.

url = "http://127.0.0.1:8008/api/scores/onboarding"

payload = {
    "currency": "USD",
    "is_manual_mode": True,
    "monthly_income": 5000,
    "monthly_expenses": 3000,
    "has_debt": "no",
    # Health defaults
    "sleep_hours": "7-8",
    # Productivity defaults
    "work_hours_per_week": "40"
}

try:
    print(f"Sending POST to {url}...")
    response = requests.post(url, json=payload, timeout=10)
    print(f"Status Code: {response.status_code}")
    try:
        print("Response JSON:", response.json())
    except:
        print("Response Text:", response.text)
except Exception as e:
    print(f"Error: {e}")
