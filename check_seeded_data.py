import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Use the Direct TCP URL from fallback script
DB_URL = "postgresql+psycopg2://postgres:LfsdSecure2024!@136.119.201.13:5432/lfsd"

def check_data():
    try:
        engine = create_engine(DB_URL)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        
        email = "time@helm.com"
        print(f"Checking user: {email}...")
        
        # 1. Check User
        user = db.execute(text("SELECT id, email FROM users WHERE email = :email"), {"email": email}).fetchone()
        if not user:
            print("❌ User NOT found!")
            return
        
        user_id = user[0]
        print(f"✅ User found: {user_id}")
        
        # 2. Check VivIndex (Score)
        # Note: VivIndex usually stores floats: financial_score, health_score, time_score
        scores = db.execute(text("SELECT * FROM viv_indexes WHERE user_id = :uid ORDER BY timestamp DESC LIMIT 1"), {"uid": str(user_id)}).fetchone()
        if scores:
             # Map columns by index or name. Let's print raw.
             print(f"✅ VivIndex found: {scores}")
        else:
             print("❌ VivIndex NOT found!")

        # 3. Check FinancialScore
        fs = db.execute(text("SELECT overall_score FROM financial_scores WHERE user_id = :uid ORDER BY timestamp DESC LIMIT 1"), {"uid": str(user_id)}).fetchone()
        if fs:
            print(f"✅ FinancialScore found: {fs[0]}")
        else:
            print("❌ FinancialScore NOT found")

        # 4. Check TimeProfile
        tp = db.execute(text("SELECT * FROM time_profiles WHERE user_id = :uid"), {"uid": str(user_id)}).fetchone()
        if tp:
            print(f"✅ TimeProfile found.")
        else:
            print("❌ TimeProfile NOT found")
            
        # 5. Check TimeEvents
        te = db.execute(text("SELECT count(*) FROM calendar_events WHERE user_id = :uid"), {"uid": str(user_id)}).fetchone()
        print(f"✅ Calendar Events count: {te[0]}")
        
        db.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_data()
