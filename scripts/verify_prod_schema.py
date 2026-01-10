import sys
import os
from sqlalchemy import create_engine, text

# Add parent directory to path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "backend"))

DATABASE_URL = "postgresql+psycopg2://postgres:LfsdSecure2024!@136.119.201.13:5432/lfsd"

def verify_schema():
    print(f"Connecting to database to verify schema...")
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # Check for column existence
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='account_status'
            """))
            row = result.fetchone()
            
            if row:
                print("✅ SUCCESS: Column 'account_status' found in 'users' table.")
            else:
                print("❌ FAILURE: Column 'account_status' NOT found in 'users' table.")
                sys.exit(1)
                
        except Exception as e:
            print(f"Verification failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    verify_schema()
