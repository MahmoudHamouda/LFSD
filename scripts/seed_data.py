from database import SessionLocal, init_db
from models import DBUser, DBFinancial, DBTransaction, DBOrder, DBNotification, DBActivity
from datetime import datetime
import uuid

def seed():
    print("Initializing database...")
    init_db()
    db = SessionLocal()
    
    user_id = "user-123"
    
    # Check if user exists
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not user:
        print("Creating user...")
        user = DBUser(id=user_id, username="alice", email="alice@example.com", preferences='{"theme": "dark"}')
        db.add(user)
        
        print("Creating financials...")
        fin = DBFinancial(user_id=user_id, income=5000.0, expenses=2000.0, savings=15000.0, debts=0.0)
        db.add(fin)
        
        print("Creating transactions...")
        db.add(DBTransaction(id=str(uuid.uuid4()), user_id=user_id, amount=12.50, category="Transport", description="Uber Ride"))
        db.add(DBTransaction(id=str(uuid.uuid4()), user_id=user_id, amount=45.00, category="Food", description="Grocery Store"))
        
        print("Creating orders...")
        db.add(DBOrder(id=str(uuid.uuid4()), user_id=user_id, partner="Uber", status="Completed", details='{"ride_type": "UberX"}'))
        
        print("Creating notifications...")
        db.add(DBNotification(id=str(uuid.uuid4()), user_id=user_id, message="Your ride has arrived", read_status=False))
        
        print("Creating activity...")
        db.add(DBActivity(id=str(uuid.uuid4()), user_id=user_id, action="Booked Ride", details="UberX to Downtown"))
        
        db.commit()
        print("Seeding complete.")
    else:
        print("User already exists. Skipping seed.")
    
    db.close()

if __name__ == "__main__":
    seed()
