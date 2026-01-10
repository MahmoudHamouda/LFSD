
import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.join(os.getcwd(), 'backend'))
sys.path.append(os.getcwd())

from backend.models.logging_models import BugReport, Base
from backend.services.bug_service import BugService

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Ensure tables created
Base.metadata.create_all(bind=engine)

def verify_bug_report():
    db = SessionLocal()
    try:
        service = BugService(db)
        print("[ACTION] Creating Bug Report...")
        report = service.create_report(
            error_message="Test Error",
            stack_trace="Traceback...",
            user_id="user-123",
            context={"foo": "bar"}
        )
        
        print("[VERIFY] Checking DB...")
        saved = db.query(BugReport).first()
        if saved:
            print("✅ SUCCESS: Bug Report found!")
            print(f"   - User ID: {saved.user_id} (Type: {type(saved.user_id)})")
            print(f"   - Error: {saved.error_message}")
        else:
            print("❌ FAILURE: Bug Report not found")
            exit(1)

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    verify_bug_report()
