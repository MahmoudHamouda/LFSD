import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database import SessionLocal
from models.models import User
from core.authentication import verify_password, get_password_hash

def check_login():
    db = SessionLocal()
    try:
        # Check correct email
        email_correct = "steward@helm.com"
        user = db.query(User).filter(User.email == email_correct).first()
        if user:
            print(f"✅ User found: {email_correct}")
            is_valid = verify_password("P@ssword123", user.hashed_password)
            print(f"Password 'P@ssword123' valid? {is_valid}")
        else:
            print(f"❌ User NOT found: {email_correct}")

        # Check incorrect email (what user likely typed)
        email_wrong = "user-steward@helm.com"
        user_wrong = db.query(User).filter(User.email == email_wrong).first()
        if user_wrong:
            print(f"⚠️  User found for: {email_wrong} (Unexpected)")
        else:
            print(f"ℹ️  User NOT found for: {email_wrong} (Expected)")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_login()
