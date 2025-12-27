
import sys
import os
from dotenv import load_dotenv

# Add the root directory to sys.path to find 'backend'
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(root_dir)

# Load .env from root
load_dotenv(os.path.join(root_dir, '.env'))

from backend.models.database import SessionLocal
from backend.models.models import User

def list_users():
    print("Starting user list...")
    try:
        db = SessionLocal()
        print(f"Connected to database. Engine: {db.bind.url}")
        users = db.query(User).all()
        print(f"Total Users Found: {len(users)}")
        for u in users:
            print(f"- {u.email} (ID: {u.id})")
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    list_users()
