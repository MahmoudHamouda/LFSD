from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    JSON,
    Index,
    UniqueConstraint
)
from models.database import Base
from sqlalchemy.sql import func
import uuid

class Notification(Base):
    """
    Unified Notification Model.
    Refactored with UUID identifiers, timezone-aware timestamps, indexing, 
    and deduplication protection.
    """
    __tablename__ = "notifications_v3"

    # UUID primary key for cross-service consistency
    notification_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # user_id is a String to match users_service_v3. 
    # ForeignKeys are avoided across microservice-style boundaries unless on shared monolith DB.
    user_id = Column(String, nullable=False, index=True)
    
    message = Column(String(500), nullable=False)
    notification_type = Column(String(50), nullable=False, index=True) # e.g., "reminder", "system"
    
    # Consistently named field to match API
    metadata = Column(JSON, nullable=False, server_default='{}') 
    
    read_status = Column(Boolean, default=False, index=True)
    
    # Idempotency key for deduplication guard (e.g. hash of user_id + message + type + date)
    idempotency_key = Column(String, unique=True, index=True, nullable=True)

    # Timezone-aware audit logs
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_user_unread_v3', 'user_id', 'read_status'),
    )

    def to_dict(self):
        """Serializes the model to a JSON-compatible dictionary."""
        return {
            "notification_id": self.notification_id,
            "user_id": self.user_id,
            "message": self.message,
            "type": self.notification_type,
            "metadata": self.metadata or {},
            "read_status": self.read_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
