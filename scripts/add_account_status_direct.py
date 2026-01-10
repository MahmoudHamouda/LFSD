import sys
import os
from sqlalchemy import create_engine, text

# Add parent directory to path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "backend"))

# Use the direct connection string found in check_db_state.py
DATABASE_URL = "postgresql+psycopg2://postgres:LfsdSecure2024!@136.119.201.13:5432/lfsd"

def add_column():
    print(f"Connecting to database at {DATABASE_URL}...")
    engine = create_engine(DATABASE_URL)
    
    print("Attempting to add account_status column to users table...")
    with engine.connect() as conn:
        try:
            # PostgreSQL syntax
            # Using transaction to be safe
            with conn.begin():
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS account_status VARCHAR DEFAULT 'ACTIVE'"))
            print("Column 'account_status' added successfully (or already existed).")
        except Exception as e:
            print(f"Migration failed: {e}")

if __name__ == "__main__":
    add_column()
