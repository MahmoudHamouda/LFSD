import requests
import jwt
from sqlalchemy import create_engine, text

import os

# 1. Login to get Token
url = os.getenv("BACKEND_URL", "https://lfsd-backend-692544481281.us-central1.run.app") + "/api/auth/login"
payload = {
    "username": "finance@helm.com",
    "email": "finance@helm.com",
    "password": os.getenv("FINANCE_USER_PASSWORD", "dummy_pass")
}
print(f"Logging in to {url}...")

try:
    res = requests.post(url, json=payload)
    res.raise_for_status()
    token = res.json().get("access_token")
    print("Login successful. Token received.")
    
    # 2. Decode Token
    decoded = jwt.decode(token, options={"verify_signature": False})
    auth0_id = decoded.get("sub")
    print(f"Auth0 ID: {auth0_id}")
    
    # 3. Patch DB
    if auth0_id:
        DB_URL = os.getenv("DATABASE_URL", "sqlite:///./lfsd_v2.db")
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            print(f"Patching finance@helm.com with auth0_id={auth0_id}...")
            # Check if auth0_id column exists? It should (schema discovery showed it?)
            # Just try updating
            stmt = text("UPDATE users SET auth0_id = :aid WHERE email = 'finance@helm.com'")
            conn.execute(stmt, {"aid": auth0_id})
            conn.commit()
            print("Patch complete.")
            
            # Verify patch
            u = conn.execute(text("SELECT id, email, auth0_id FROM users WHERE email='finance@helm.com'")).fetchone()
            print(f"User now: {u}")
            
except Exception as e:
    print(f"Error: {e}")
