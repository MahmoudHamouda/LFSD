import sys
import os
from sqlalchemy import create_engine, text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATABASE_URL = "postgresql+psycopg2://postgres:LfsdSecure2024!@136.119.201.13:5432/lfsd"
engine = create_engine(DATABASE_URL)

def check_state():
    print("=== CHECKING DATABASE STATE ===")
    
    with engine.connect() as conn:
        # Get finance user ID
        fid = conn.execute(text("SELECT id FROM users WHERE email = 'finance@helm.com'")).scalar()
        print(f"Finance user ID: {fid}")
        
        # Check transaction count
        tx_count = conn.execute(text("SELECT COUNT(*) FROM transactions WHERE user_id = :uid"), {"uid": fid}).scalar()
        print(f"Transaction count: {tx_count}")
        
        # Check account count
        acc_count = conn.execute(text("SELECT COUNT(*) FROM financial_accounts WHERE user_id = :uid"), {"uid": fid}).scalar()
        print(f"Account count: {acc_count}")
        
        # Check distinct transaction dates
        date_count = conn.execute(text("""
            SELECT COUNT(DISTINCT DATE(transaction_date)) 
            FROM transactions 
            WHERE user_id = :uid
        """), {"uid": fid}).scalar()
        print(f"Distinct transaction dates: {date_count}")
        
        # Sample transactions
        if tx_count > 0:
            print("\nSample transactions:")
            rows = conn.execute(text("""
                SELECT merchant_name, amount, transaction_date 
                FROM transactions 
                WHERE user_id = :uid 
                ORDER BY transaction_date DESC 
                LIMIT 5
            """), {"uid": fid})
            for row in rows:
                print(f"  {row.merchant_name}: ${row.amount} on {row.transaction_date}")

if __name__ == "__main__":
    check_state()
