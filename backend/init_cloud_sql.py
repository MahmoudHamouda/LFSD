"""
Initialize Cloud SQL database schema and create test users.
Run this script to set up the database for the first time.
"""

import os
import sys

# Set Cloud SQL connection (using public IP for initialization)
os.environ["DATABASE_URL"] = "postgresql://lfsd_user:LFSDProd2026SecurePass!@136.119.201.13:5432/lfsd"

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.database import Base, engine, get_db
from models.models import User
from core.authentication import get_password_hash
import uuid

def init_cloud_sql():
    """Initialize database schema and create test user."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created successfully")
    
    # Create test user
    print("\nCreating test user finance@helm.com...")
    db = next(get_db())
    
    try:
        # Check if user exists
        existing_user = db.query(User).filter(User.email == "finance@helm.com").first()
        
        if existing_user:
            print("✓ User finance@helm.com already exists")
            # Update password
            existing_user.hashed_password = get_password_hash("password123")
            db.commit()
            print("✓ Password updated to: password123")
        else:
            new_user = User(
                id=str(uuid.uuid4()),
                email="finance@helm.com",
                hashed_password=get_password_hash("password123"),
                profile_json={"name": "Finance User"},
                onboarding_status="COMPLETED"
            )
            db.add(new_user)
            db.commit()
            print(f"✓ User created: finance@helm.com (ID: {new_user.id})")
            print("✓ Password: password123")
            
    except Exception as e:
        print(f"✗ Error creating user: {e}")
        db.rollback()
        raise
    finally:
        db.close()
    
    print("\n✓ Cloud SQL initialization complete!")

if __name__ == "__main__":
    init_cloud_sql()
