
import requests
import json
import uuid

BACKEND_URL = "https://lfsd-backend-wpvii577oq-uc.a.run.app"
LOGIN_URL = f"{BACKEND_URL}/auth/login"
SIGNUP_URL = f"{BACKEND_URL}/auth/signup"

USERS_TO_TEST = [
    {"email": "finance@helm.com", "password": "P@ssword"},
    {"email": "time@helm.com", "password": "P@ssword"},
    {"email": "Health@helm.com", "password": "P@ssword"},
    {"email": "Super@helm.com", "password": "P@ssword"}
]

def test_login(email, password):
    print(f"Testing Login for: {email}")
    try:
        payload = {"username": email, "password": password}
        response = requests.post(LOGIN_URL, json=payload, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                print(f"  [SUCCESS] {email} logged in. Token received.")
                return True
            else:
                print(f"  [FAIL] {email} logged in but no token? Response: {data}")
                return False
        else:
            print(f"  [FAIL] {email} login failed. Status: {response.status_code}. Msg: {response.text}")
            return False
    except Exception as e:
        print(f"  [ERROR] Exception testing {email}: {e}")
        return False

def test_signup():
    random_id = str(uuid.uuid4())[:8]
    email = f"testuser_{random_id}@helm.com"
    password = "NewUserPass123!"
    name = f"Test User {random_id}"
    
    print(f"\nTesting Signup for new user: {email}")
    try:
        payload = {"email": email, "password": password, "name": name}
        response = requests.post(SIGNUP_URL, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"  [SUCCESS] Signup successful for {email}.")
            # Try logging in with new user
            return test_login(email, password)
        elif response.status_code == 409:
             print(f"  [FAIL] User already exists (unexpected for random).")
             return False
        else:
             print(f"  [FAIL] Signup failed. Status: {response.status_code}. Msg: {response.text}")
             return False
    except Exception as e:
        print(f"  [ERROR] Exception testing signup: {e}")
        return False

if __name__ == "__main__":
    print(f"Target Backend: {BACKEND_URL}\n")
    
    all_passed = True
    
    # Test Existing Users
    for user in USERS_TO_TEST:
        if not test_login(user["email"], user["password"]):
            all_passed = False
            
    # Test New User
    if not test_signup():
        all_passed = False
        
    if all_passed:
        print("\nAll auth tests PASSED.")
        exit(0)
    else:
        print("\nSome auth tests FAILED.")
        exit(1)
