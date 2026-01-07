import sys
import os
import uuid
from datetime import datetime
from sqlalchemy import create_engine, text, inspect

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATABASE_URL = "postgresql+psycopg2://postgres:LfsdSecure2024!@136.119.201.13:5432/lfsd"
engine = create_engine(DATABASE_URL)

def diagnose():
    print("--- DIAGNOSING TRANSACTIONS TABLE ---")
    insp = inspect(engine)
    cols = [c['name'] for c in insp.get_columns('transactions')]
    print(f"Columns in 'transactions': {cols}")
    
    with engine.connect() as conn:
        try:
            print("Attempting minimal insert...")
            uid = conn.execute(text("SELECT id FROM users LIMIT 1")).scalar()
            
            conn.execute(text("""
                INSERT INTO transactions (id, amount, transaction_date)
                VALUES (:id, -10.0, :date)
            """), {"id": str(uuid.uuid4()), "date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")})
            print("Minimal insert success!")
            
            print("Attempting full insert...")
            conn.execute(text("""
                INSERT INTO transactions (id, user_id, amount, transaction_date, merchant_name, created_at)
                VALUES (:id, :uid, -20.0, :date, 'Test Merchant', :now)
            """), {
                "id": str(uuid.uuid4()), 
                "uid": uid,
                "date": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                "now": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            })
            print("Full insert success!")
            
            # Rollback to not pollute
            # conn.rollback() # Logic is autocommit=False usually?
            # Actually we want to commit if it works to verify constraints.
            # But let's just rollback for diagnosis.
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    diagnose()
