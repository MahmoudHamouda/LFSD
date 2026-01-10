from backend.models.database import SessionLocal
from backend.models.models import User
db = SessionLocal()
try:
    user = db.query(User).filter(User.id == "verify-user-123").first()
    if user:
        print(f"User found: {user.email}")
    else:
        print("User NOT found")
finally:
    db.close()
