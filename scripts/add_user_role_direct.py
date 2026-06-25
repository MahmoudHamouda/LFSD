import sys
import os
from sqlalchemy import create_engine, text

# Add parent directory to path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "backend"))

# Use database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./lfsd_v2.db")

def add_role_column():
    print(f"Connecting to database at {DATABASE_URL}...")
    engine = create_engine(DATABASE_URL)
    
    print("Attempting to add 'role' column to users table...")
    with engine.connect() as conn:
        try:
            with conn.begin():
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR DEFAULT 'user'"))
            print("Column 'role' added successfully (or already existed).")
        except Exception as e:
            print(f"Migration failed: {e}")

if __name__ == "__main__":
    add_role_column()
