from sqlalchemy.orm import Session
from models.models import User
from models.logging_models import AuditLog, ActivityFeed
from sqlalchemy import desc
import uuid
from datetime import datetime

class AdminService:
    def __init__(self, db: Session):
        self.db = db

    def get_users(self, skip: int = 0, limit: int = 20):
        """
        Get all users with their account status.
        """
        users = self.db.query(User).offset(skip).limit(limit).all()
        return users

    def unlock_user(self, target_user_id: str, admin_user_id: str, reason: str):
        """
        Unlock a user, emit AuditLog and ActivityFeed events.
        """
        user = self.db.query(User).filter(User.id == target_user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Check if already active
        if user.account_status == "ACTIVE":
            return user # Idempotent

        # Update Status
        old_status = user.account_status
        user.account_status = "ACTIVE"
        
        # Emit Audit Log
        audit = AuditLog(
            id=str(uuid.uuid4()),
            actor_id=admin_user_id,
            actor_type="admin",
            action="UPDATE",
            entity_type="User",
            entity_id=target_user_id,
            changes_json={"account_status": {"old": old_status, "new": "ACTIVE"}, "reason": reason}
        )
        self.db.add(audit)
        
        # Emit Activity Feed (User visible)
        feed = ActivityFeed(
            user_id=target_user_id,
            action_type="ACCOUNT_UNLOCKED",
            description="Your account has been manually unlocked by support.",
            metadata_json={"reason": reason},
            is_read=False
        )
        self.db.add(feed)
        
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_audit_logs(self, limit: int = 50):
        """
        Get recent audit logs.
        """
        return self.db.query(AuditLog).order_by(desc(AuditLog.timestamp)).limit(limit).all()
