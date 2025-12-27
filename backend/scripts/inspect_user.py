
import sys
import os
import logging

# Disable logging
logging.basicConfig(level=logging.CRITICAL)
logging.getLogger('sqlalchemy.engine').setLevel(logging.CRITICAL)

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database import SessionLocal
from models.models import User

def check_user():
    try:
        db = SessionLocal()
        user = db.query(User).filter(User.email == "steward@helm.com").first()
        if user:
            print(f"USER_FOUND: {user.email}")
            print(f"HASH: [{user.hashed_password}]")
        else:
            print("USER_NOT_FOUND")
        db.close()
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    check_user()
