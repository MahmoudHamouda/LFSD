
import sys
import os
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))
sys.path.append(os.getcwd())

from backend.models.models import Base, User
from backend.models.logging_models import AuditLog, ActivityFeed
from backend.services.admin_service import AdminService
from backend.models.database import Base # Ensure shared Base

# Setup Test DB (Memory)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# CREATE TABLES
Base.metadata.create_all(bind=engine)

def verify_admin_ops():
    db = SessionLocal()
    try:
        # 1. Setup Data
        admin_id = "admin-001"
        target_id = "user-locked"
        
        # User defaults to ACTIVE? But I want to test UNLOCK.
        # So I will set status to LOCKED manually.
        user = User(id=target_id, email="locked@test.com", account_status="LOCKED")
        db.add(user)
        db.commit()
        
        print(f"[SETUP] Created locked user '{target_id}' with status '{user.account_status}'")
        
        # 2. Unlock User
        service = AdminService(db)
        print("[ACTION] Unlocking user...")
        updated_user = service.unlock_user(target_id, admin_id, "Forgot password")
        
        # 3. Verify User Status
        print(f"[VERIFY] User status is now: {updated_user.account_status}")
        if updated_user.account_status != "ACTIVE":
            print("❌ FAILURE: User status not updated to ACTIVE")
            exit(1)
            
        # 4. Verify Audit Log
        print("[VERIFY] Checking Audit Log...")
        audit = db.query(AuditLog).filter(AuditLog.entity_id == target_id).first()
        if audit:
            print("✅ SUCCESS: Audit Log found!")
            print(f"   - Action: {audit.action}")
            print(f"   - Actor: {audit.actor_id}")
            print(f"   - Changes: {audit.changes_json}")
        else:
            print("❌ FAILURE: Audit Log not found")
            exit(1)
            
        # 5. Verify Activity Feed
        print("[VERIFY] Checking Activity Feed...")
        feed = db.query(ActivityFeed).filter(ActivityFeed.user_id == target_id).first()
        if feed:
            print("✅ SUCCESS: Activity Feed found!")
            print(f"   - Description: {feed.description}")
        else:
             print("❌ FAILURE: Activity Feed not found")
             exit(1)

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    verify_admin_ops()
