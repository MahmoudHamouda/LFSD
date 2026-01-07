"""
Standalone Financial Data Seeder - 30 Day History
Creates financial accounts and transactions for finance@helm.com with 30 days of data
"""
import sys
import os
import random
import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATABASE_URL = "postgresql+psycopg2://postgres:LfsdSecure2024!@136.119.201.13:5432/lfsd"
engine = create_engine(DATABASE_URL)

def seed_finance_30_days():
    print("=== SEEDING 30 DAYS OF FINANCIAL DATA ===")
    
    with engine.connect() as conn:
        # Get finance user ID
        fid = conn.execute(text("SELECT id FROM users WHERE email = 'finance@helm.com'")).scalar()
        if not fid:
            print("ERROR: finance@helm.com user not found!")
            return
            
        print(f"Finance user ID: {fid}")
        
        # 1. Create a financial account if it doesn't exist
        existing_account = conn.execute(text("""
            SELECT id FROM financial_accounts WHERE user_id = :uid LIMIT 1
        """), {"uid": fid}).scalar()
        
        if existing_account:
            print(f"Using existing account: {existing_account}")
            acct_id = existing_account
        else:
            acct_id = str(uuid.uuid4())
            print(f"Creating new account: {acct_id}")
            conn.execute(text("""
                INSERT INTO financial_accounts (id, user_id, name, type, balance, currency, institution_name, created_at)
                VALUES (:id, :uid, 'Primary Checking', 'depository', 5000.00, 'USD', 'Chase Bank', :now)
            """), {
                "id": acct_id, 
                "uid": fid, 
                "now": datetime.utcnow()
            })
            print("Account created successfully")
        
        # 2. Clear existing transactions for this user to avoid duplicates
        deleted = conn.execute(text("DELETE FROM transactions WHERE user_id = :uid"), {"uid": fid})
        print(f"Cleared {deleted.rowcount} existing transactions")
        
        # 3. Create 30 days of transaction history
        print("Creating 30 days of transactions...")
        merchants = [
            ("Whole Foods", "Food & Dining"),
            ("Starbucks", "Food & Dining"),
            ("Shell Gas", "Transportation"),
            ("Amazon", "Shopping"),
            ("Netflix", "Entertainment"),
            ("Uber", "Transportation"),
            ("Target", "Shopping")
        ]
        
        transaction_count = 0
        for day_offset in range(30):
            tx_date = datetime.utcnow() - timedelta(days=day_offset)
            
            # Weekly salary (every 7 days)
            if day_offset % 7 == 0:
                conn.execute(text("""
                    INSERT INTO transactions (
                        id, account_id, user_id, amount, currency_code, transaction_date,
                        description, merchant_name, category_primary, is_recurring, created_at
                    ) VALUES (
                        :id, :aid, :uid, :amt, 'USD', :date,
                        :desc, :merch, :cat, false, :now
                    )
                """), {
                    "id": str(uuid.uuid4()),
                    "aid": acct_id,
                    "uid": fid,
                    "amt": 3000.00,  # Positive for income
                    "date": tx_date,
                    "desc": "Bi-weekly Salary",
                    "merch": "Employer Inc",
                    "cat": "Income",
                    "now": datetime.utcnow()
                })
                transaction_count += 1
            
            # Daily expenses (1-2 per day)
            num_daily_tx = random.randint(1, 2)
            for _ in range(num_daily_tx):
                merchant, category = random.choice(merchants)
                amount = -random.uniform(10.0, 150.0)  # Negative for expenses
                
                conn.execute(text("""
                    INSERT INTO transactions (
                        id, account_id, user_id, amount, currency_code, transaction_date,
                        description, merchant_name, category_primary, is_recurring, created_at
                    ) VALUES (
                        :id, :aid, :uid, :amt, 'USD', :date,
                        :desc, :merch, :cat, false, :now
                    )
                """), {
                    "id": str(uuid.uuid4()),
                    "aid": acct_id,
                    "uid": fid,
                    "amt": round(amount, 2),
                    "date": tx_date,
                    "desc": f"Purchase at {merchant}",
                    "merch": merchant,
                    "cat": category,
                    "now": datetime.utcnow()
                })
                transaction_count += 1
        
        conn.commit()
        print(f"✅ Successfully created {transaction_count} transactions across 30 days")
        
        # 4. Verify the data
        print("\n=== VERIFICATION ===")
        total_tx = conn.execute(text("SELECT COUNT(*) FROM transactions WHERE user_id = :uid"), {"uid": fid}).scalar()
        distinct_dates = conn.execute(text("""
            SELECT COUNT(DISTINCT DATE(transaction_date)) 
            FROM transactions 
            WHERE user_id = :uid
        """), {"uid": fid}).scalar()
        
        print(f"Total transactions: {total_tx}")
        print(f"Distinct dates: {distinct_dates}")
        
        # Sample recent transactions
        print("\nRecent transactions:")
        rows = conn.execute(text("""
            SELECT merchant_name, amount, transaction_date 
            FROM transactions 
            WHERE user_id = :uid 
            ORDER BY transaction_date DESC 
            LIMIT 5
        """), {"uid": fid})
        
        for row in rows:
            print(f"  {row.merchant_name}: ${row.amount:.2f} on {row.transaction_date}")

if __name__ == "__main__":
    try:
        seed_finance_30_days()
        print("\n✅ SEEDING COMPLETE")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
