"""
Direct Cloud SQL Seeding Script
Connects directly to production Cloud SQL and seeds users.
"""

from google.cloud.sql.connector import Connector
import pg8000
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import uuid

# Import seeding logic
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.models import User, LifeGoal, VivIndex
from core.authentication import get_password_hash

# Cloud SQL Connection Details
INSTANCE_CONNECTION_NAME = "newprojectlfsd:us-central1:lfsd-postgres-prod"
DB_USER = "postgres"
DB_PASS = "LfsdSecure2024!"
DB_NAME = "lfsd"

def get_cloud_sql_engine():
    """Create SQLAlchemy engine connected to Cloud SQL."""
    connector = Connector()
    
    def getconn():
        conn = connector.connect(
            INSTANCE_CONNECTION_NAME,
            "pg8000",
            user=DB_USER,
            password=DB_PASS,
            db=DB_NAME,
            ip_type="public"
        )
        return conn
    
    engine = sqlalchemy.create_engine(
        "postgresql+pg8000://",
        creator=getconn,
    )
    return engine

def seed_users_directly():
    """Seed users directly into Cloud SQL production database."""
    print("Connecting to Cloud SQL...")
    engine = get_cloud_sql_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        users_to_create = [
            {
                "id": "user-finance",
                "email": "finance@helm.com",
                "password": "P@ssword123",
                "name": "Finance User",
            },
            {
                "id": "user-empty",
                "email": "empty@helm.com",
                "password": "P@ssword123",
                "name": "Empty User",
            },
            {
                "id": "user-health",
                "email": "health@helm.com",
                "password": "P@ssword123",
                "name": "Health User",
            },
            {
                "id": "user-time",
                "email": "time@helm.com",
                "password": "P@ssword123",
                "name": "Time User",
            },
            {
                "id": "user-super",
                "email": "super@helm.com",
                "password": "P@ssword123",
                "name": "Super User",
            },
            {
                "id": "user-david",
                "email": "david@example.com",
                "password": "password",
                "name": "David",
            },
            {
                "id": "user-sara",
                "email": "sara@example.com",
                "password": "password",
                "name": "Sara",
            },
            {
                "id": "user-alex",
                "email": "alex@example.com",
                "password": "password",
                "name": "Alex",
            }
        ]
        
        print(f"\nSeeding {len(users_to_create)} users...")
        
        for user_data in users_to_create:
            existing = db.query(User).filter(User.email == user_data["email"]).first()
            
            if existing:
                print(f"  ✓ {user_data['email']} already exists (ID: {existing.id})")
            else:
                print(f"  + Creating {user_data['email']}...")
                user = User(
                    id=user_data["id"],
                    email=user_data["email"],
                    hashed_password=get_password_hash(user_data["password"]),
                    profile_json={"name": user_data["name"]},
                    onboarding_status="COMPLETE"
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                
                # Add VivIndex for each user
                viv_index = VivIndex(
                    id=str(uuid.uuid4()),
                    user_id=user.id,
                    financial_score=50.0,
                    health_score=50.0,
                    time_score=50.0,
                    snapshot_reason="Initial Seeding",
                    timestamp=datetime.utcnow()
                )
                db.add(viv_index)
                db.commit()
                print(f"    ✓ Created with VivIndex")
        
        print("\n✅ Seeding completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("="*60)
    print("Direct Cloud SQL Seeding")
    print("="*60)
    success = seed_users_directly()
    
    if success:
        print("\n🎉 You can now run E2E tests!")
    else:
        print("\n⚠️ Seeding failed. Check error above.")
