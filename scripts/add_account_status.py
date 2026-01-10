import sys
import os
from sqlalchemy import text

# Add parent directory to path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "backend"))

from backend.models.database import engine

def add_column():
    print("Attempting to add account_status column to users table...")
    with engine.connect() as conn:
        try:
            # Check if column exists first to avoid error? 
            # Or just try ADD COLUMN and catch
            # PostgreSQL syntax
            conn.execute(text("ALTER TABLE users ADD COLUMN account_status VARCHAR DEFAULT 'ACTIVE'"))
            conn.commit()
            print("Column 'account_status' added successfully.")
        except Exception as e:
            print(f"Migration failed (might already exist): {e}")

if __name__ == "__main__":
    add_column()
