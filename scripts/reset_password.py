
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add current directory (backend) to sys.path so that absolute imports works
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from backend.models.models import User
from backend.core.authentication import get_password_hash
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def reset_password(email, new_password):
    if not DATABASE_URL:
        print("DATABASE_URL not found.")
        return

    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        user = session.query(User).filter(User.email == email).first()
        if not user:
            print(f"User {email} not found.")
            return

        print(f"Resetting password for {email}...")
        hashed = get_password_hash(new_password)
        user.hashed_password = hashed
        session.commit()
        print(f"Password for {email} has been reset to '{new_password}'.")
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    reset_password("finance@helm.com", "password123")
