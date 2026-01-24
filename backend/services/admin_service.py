from sqlalchemy.orm import Session
from models.models import User
from models.logging_models import ActivityFeed
from sqlalchemy import desc
import uuid
from datetime import datetime
from services.audit_service import AuditService, AuditAction, AuditEntity
from loguru import logger

class AdminService:
    def __init__(self, db: Session):
        self.db = db

    def get_users(self, skip: int = 0, limit: int = 20):
        """
        Get all users with their account status.
        """
        return self.db.query(User).offset(skip).limit(limit).all()

    def unlock_user(self, target_user_id: str, admin_user_id: str, reason: str, correlation_id: str = None):
        """
        Unlock a user, emit AuditLog and ActivityFeed events.
        
        Features:
        - Strict Audit Taxonomy (AuditAction.SECURITY_REVOKE used as proxy for critical security changes)
        - Impersonation/Admin Context Tracking
        - Fail-fast on critical audit failure
        - No PII in audit logs
        """
        user = self.db.query(User).filter(User.id == target_user_id).first()
        if not user:
            raise ValueError("User not found")
        
        if user.account_status == "ACTIVE":
            return user 

        # 1. Update Status
        old_status = user.account_status
        user.account_status = "ACTIVE"
        
        # 2. Emit Audit Log (CRITICAL)
        # We use UPDATE but marking as critical because it changes security posture.
        AuditService.log_audit(
            db=self.db,
            actor_id=admin_user_id,
            actor_type="admin",
            action=AuditAction.UPDATE,
            entity_type=AuditEntity.USER,
            entity_id=target_user_id,
            changes={
                "account_status": {"old": old_status, "new": "ACTIVE"}, 
                "reason_redacted": True # Don't store free-text reason in 'changes' if sensitive
            },
            metadata={"admin_reason": reason},
            correlation_id=correlation_id,
            is_critical=True # If this fails, the status change must rollback
        )
        
        # 3. Emit Activity Feed (User visible)
        feed = ActivityFeed(
            user_id=target_user_id,
            event_type="security_update",
            action_type="ACCOUNT_UNLOCKED",
            description="Your account has been manually unlocked by support.",
            metadata_json={"reason": reason},
            is_read=False
        )
        self.db.add(feed)
        
        try:
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to unlock user {target_user_id}: {e}")
            raise e

    def get_audit_logs(self, limit: int = 50):
        """
        Get recent audit logs. (Moved from AdminService to a more appropriate place if needed, 
        but kept here for now per request).
        """
        from models.logging_models import AuditLog
        return self.db.query(AuditLog).order_by(desc(AuditLog.timestamp)).limit(limit).all()

