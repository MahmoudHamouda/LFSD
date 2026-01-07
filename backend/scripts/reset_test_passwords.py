
import sys
import os
import bcrypt
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Direct connection (Fallback IP from previous step)
DB_URL = "postgresql+psycopg2://postgres:LfsdSecure2024!@136.119.201.13/lfsd"

def reset_passwords():
    print("Connecting to DB...")
    engine = create_engine(DB_URL)
    conn = engine.connect()
    
    # Generate hash for "P@ssword123"
    # bcrypt.hashpw requires bytes
    hashed = bcrypt.hashpw(b"P@ssword123", bcrypt.gensalt()).decode('utf-8')
    print(f"Generated hash for 'P@ssword123': {hashed}")
    
    target_emails = [
        "empty@helm.com", 
        "finance@helm.com", 
        "health@helm.com", 
        "time@helm.com", 
        "super@helm.com"
    ]
    
    print("Updating passwords...")
    for email in target_emails:
        try:
            query = text("UPDATE users SET hashed_password = :h WHERE email = :e")
            conn.execute(query, {"h": hashed, "e": email})
            print(f"Updated {email}")
        except Exception as e:
            print(f"Failed to update {email}: {e}")
            
    conn.commit()
    conn.close()
    print("Done.")

if __name__ == "__main__":
    reset_passwords()
