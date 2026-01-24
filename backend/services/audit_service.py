import logging
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
from typing import Optional, Dict, Any, Literal
from models.logging_models import AuditLog

logger = logging.getLogger("audit_service")

# Action Taxonomy
class AuditAction:
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    EXECUTE = "EXECUTE"
    LOGIN = "LOGIN"
    PAYMENT = "PAYMENT"
    SUBSCRIPTION_CHANGE = "SUBSCRIPTION_CHANGE"
    SECURITY_REVOKE = "SECURITY_REVOKE"
    VIEW = "VIEW" # Low criticality

class AuditEntity:
    USER = "USER"
    ORDER = "ORDER"
    TRANSACTION = "TRANSACTION"
    SUBSCRIPTION = "SUBSCRIPTION"
    CONNECTION = "CONNECTION"
    GOAL = "GOAL"
    SYSTEM = "SYSTEM"

class AuditService:
    @staticmethod
    def log_audit(
        db: Session,
        actor_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        changes: Optional[Dict[str, Any]] = None,
        actor_type: str = "user",
        metadata: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        request_id: Optional[str] = None,
        is_critical: bool = False
    ) -> Optional[AuditLog]:
        """
        Emits a business audit event.
        
        Rules:
        1. If is_critical=True, failures will raise exceptions to rollback the main transaction.
        2. Normalizes action strings to the taxonomy.
        3. Includes correlation and request IDs for tracing.
        """
        # Normalize action to uppercase
        action = action.upper().strip()
        
        # Enforce criticality for specific actions automatically
        if action in [AuditAction.PAYMENT, AuditAction.SUBSCRIPTION_CHANGE, AuditAction.SECURITY_REVOKE]:
            is_critical = True

        try:
            # Ensure metadata captures traceability
            actual_metadata = metadata or {}
            if correlation_id: actual_metadata["correlation_id"] = correlation_id
            if request_id: actual_metadata["request_id"] = request_id

            audit = AuditLog(
                id=str(uuid.uuid4()),
                actor_id=actor_id,
                actor_type=actor_type,
                action=action,
                entity_type=entity_type.upper().strip(),
                entity_id=str(entity_id),
                changes_json=changes,
                metadata_json=actual_metadata,
                timestamp=datetime.utcnow(),
                correlation_id=correlation_id
            )
            db.add(audit)
            
            # Use separate non-blocking logging for emission if needed, 
            # but DB state is the source of truth.
            return audit
            
        except Exception as e:
            logger.error(f"Failed to create audit log for {action} on {entity_type}: {e}")
            if is_critical:
                # Fail the entire transaction if audit logging is critical
                raise RuntimeError(f"Critical Audit Failure: {e}")
            return None

