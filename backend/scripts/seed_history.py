import sys
import os
import random
import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

# Add parent directory to path to allow imports if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Direct connection
DATABASE_URL = "postgresql+psycopg2://postgres:LfsdSecure2024!@136.119.201.13:5432/lfsd"
engine = create_engine(DATABASE_URL)

def seed_history():
    print("--- SEEDING 30-DAY HISTORY (v2: String Dates) ---")
    
    with engine.connect() as conn:
        # Get User IDs
        users = {}
        result = conn.execute(text("SELECT email, id FROM users WHERE email IN ('finance@helm.com', 'health@helm.com', 'time@helm.com')"))
        for row in result:
            users[row.email] = row.id
            
        print(f"Found users: {users}")
        
        # 1. FINANCE HISTORY (finance@helm.com)
        fid = users.get('finance@helm.com')
        if fid:
            print("Seeding Finance History...")
            # Get an account
            aid = conn.execute(text("SELECT id FROM financial_accounts WHERE user_id = :uid LIMIT 1"), {"uid": fid}).scalar()
            if not aid:
                aid = str(uuid.uuid4())
                conn.execute(text("INSERT INTO financial_accounts (id, user_id, type, balance) VALUES (:id, :uid, 'check', 5000)"), {"id": aid, "uid": fid})
            
            # Insert 30 days of transactions
            for day in range(30):
                # Calculate dates, formatted as string for safety
                dt_obj = datetime.utcnow() - timedelta(days=day)
                date_str = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
                
                # Salary weekly
                if day % 7 == 0:
                    conn.execute(text("""
                        INSERT INTO transactions (id, account_id, amount, transaction_date, description, merchant_name, category_primary, created_at)
                        VALUES (:id, :aid, 3000, :date, 'Weekly Salary', 'Employer Inc', 'Salary', :now)
                    """), {"id": str(uuid.uuid4()), "aid": aid, "date": date_str, "now": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")})
                
                # Daily Spend
                conn.execute(text("""
                    INSERT INTO transactions (id, account_id, amount, transaction_date, description, merchant_name, category_primary, created_at)
                    VALUES (:id, :aid, :amt, :date, :desc, :merch, 'Food & Dining', :now)
                """), {
                    "id": str(uuid.uuid4()), "aid": aid, "amt": -random.randint(15, 60), 
                    "date": date_str, "now": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                    "desc": f"Grocery Day {day}", "merch": "Whole Foods"
                })
        
        # 2. HEALTH HISTORY (health@helm.com)
        hid = users.get('health@helm.com')
        if hid:
            print("Seeding Health History...")
            for day in range(30):
                date_obj = (datetime.utcnow() - timedelta(days=day)).date()
                date_str = date_obj.strftime("%Y-%m-%d") # Format as Date string
                
                # Check exist
                exists = conn.execute(text("SELECT 1 FROM health_daily_summaries WHERE user_id=:uid AND date=:date"), {"uid": hid, "date": date_str}).scalar()
                if not exists:
                    # Note: Assuming 'date' column in health_daily_summaries is DATE or DATETIME compatible with 'YYYY-MM-DD'
                    conn.execute(text("""
                        INSERT INTO health_daily_summaries (id, user_id, date, steps_count, sleep_duration_minutes, sleep_quality_score, hrv_average)
                        VALUES (:id, :uid, :date, :steps, :sleep, :qual, :hrv)
                    """), {
                        "id": str(uuid.uuid4()), "uid": hid, "date": date_str,
                        "steps": random.randint(8000, 12000), "sleep": 480, "qual": 85, "hrv": 60
                    })

        # 3. TIME HISTORY (time@helm.com)
        tid = users.get('time@helm.com')
        if tid:
            print("Seeding Time History...")
            # Time relies on TimeProfile mostly, but let's ensure one exists
            conn.execute(text("""
                INSERT INTO time_profiles (id, user_id, work_hours_per_week, routine_style, task_style)
                VALUES (:id, :uid, 40, 'Structured', 'Planned')
                ON CONFLICT (id) DO NOTHING
            """), {"id": str(uuid.uuid4()), "uid": tid})

        conn.commit()
    print("Seeding Complete.")

if __name__ == "__main__":
    seed_history()
