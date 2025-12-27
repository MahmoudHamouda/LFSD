from models.database import SessionLocal
from models.models import User

db = SessionLocal()
users = db.query(User).all()
print(f"Total Users: {len(users)}")
for u in users:
    print(f"- {u.email} (ID: {u.id})")
db.close()
