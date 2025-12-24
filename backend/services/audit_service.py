import logging
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
from models.logging_models import AuditLog

logger = logging.getLogger("audit_service")

class AuditService:
    @staticmethod
    def log_audit(
        db: Session,
        actor_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        changes: dict = None,
        actor_type: str = "user",
        metadata: dict = None
    ):
        """
        Emits a business audit event.
        Does NOT commit immediately to allow bundling with the main transaction.
        """
        try:
            audit = AuditLog(
                id=str(uuid.uuid4()),
                actor_id=actor_id,
                actor_type=actor_type,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                changes_json=changes,
                metadata_json=metadata,
                timestamp=datetime.utcnow()
            )
            db.add(audit)
            logger.info(f"AUDIT: {action} {entity_type} {entity_id} by {actor_id}")
            return audit
        except Exception as e:
            logger.error(f"Failed to create audit log: {e}")
            return None
