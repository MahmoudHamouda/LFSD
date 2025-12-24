import requests
import sys
import uuid

BASE_URL = "http://localhost:8003/api"
# Specific email from user screenshot to reproduce 500
EMAIL = "ham@ham.com"
PASSWORD = "Password123!"
NAME = "Ham"

def simulate_signup():
    print(f"--- Simulating Signup for {EMAIL} ---")
    
    try:
        response = requests.post(f"{BASE_URL}/auth/signup", json={
            "email": EMAIL,
            "password": PASSWORD,
            "name": NAME
        })
        
        print(f"Status Code: {response.status_code}")
        try:
            print("JSON Response:", response.json())
        except:
            print("Raw Text Response (First 2000 chars):")
            print(response.text[:2000])
            
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    simulate_signup()
