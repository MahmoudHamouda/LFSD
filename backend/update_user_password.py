from models.database import SessionLocal
from models.models import User
from core.authentication import get_password_hash

def update_password():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == "verify-user-123").first()
        if user:
            print(f"Updating password for {user.email}")
            user.hashed_password = get_password_hash("password123")
            db.commit()
            print("Password updated successfully.")
        else:
            print("User verify-user-123 not found!")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    update_password()
