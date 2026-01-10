import sys
import os
from sqlalchemy import create_engine, text

# Add parent directory to path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, "backend"))

# Use the direct connection string
DATABASE_URL = "postgresql+psycopg2://postgres:LfsdSecure2024!@136.119.201.13:5432/lfsd"

def promote_admin(email: str):
    print(f"Connecting to database...")
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        try:
            # Check if user exists
            result = conn.execute(text("SELECT id, role FROM users WHERE email = :email"), {"email": email})
            user = result.fetchone()
            
            if not user:
                print(f"❌ Error: User with email '{email}' not found.")
                return

            print(f"Found user {user.id} with current role: {user.role}")
            
            if user.role == 'admin':
                print("User is already an admin.")
                return

            # Update role
            with conn.begin():
                conn.execute(text("UPDATE users SET role = 'admin' WHERE email = :email"), {"email": email})
            
            print(f"✅ SUCCESS: User '{email}' promoted to ADMIN.")
            
        except Exception as e:
            print(f"❌ Operation failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/promote_admin.py <email>")
        sys.exit(1)
    
    email_arg = sys.argv[1]
    promote_admin(email_arg)
