"""
Logging Models - System logs, bug reports, audit logs, activity feed, and notifications.

Provides core infrastructure for observability and user engagement.
All models use timezone-aware timestamps and proper enums for type safety.
"""

import enum
import uuid
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


# ============================================================================
# ENUMS
# ============================================================================

class LogLevel(str, enum.Enum):
    """System log severity levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class BugStatus(str, enum.Enum):
    """Bug report lifecycle states."""
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    IGNORED = "IGNORED"


class BugSeverity(str, enum.Enum):
    """Bug severity classification."""
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


# ============================================================================
# MODELS
# ============================================================================

class SystemLog(Base):
    """Application-level system logs for debugging and monitoring."""
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    level = Column(Enum(LogLevel), default=LogLevel.INFO, nullable=False, index=True)
    message = Column(Text, nullable=False)

    module = Column(String(255), index=True, nullable=True)
    function_name = Column(String(255), nullable=True)
    line_number = Column(Integer, nullable=True)

    request_id = Column(String(100), index=True, nullable=True)
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=True, index=True)

    extra_data = Column(JSON, nullable=False, default=dict)


class BugReport(Base):
    """User-reported and system-detected bugs."""
    __tablename__ = "bug_reports"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), 
                       onupdate=func.now(), nullable=False)

    error_type = Column(String(255), index=True, nullable=True)
    error_message = Column(Text, nullable=False)

    severity = Column(Enum(BugSeverity), default=BugSeverity.ERROR, nullable=False)
    status = Column(Enum(BugStatus), default=BugStatus.OPEN, nullable=False, index=True)

    stack_trace = Column(Text, nullable=True)  # Nullable for manual reports
    source_file = Column(String(255), nullable=True)
    line_number = Column(Integer, nullable=True)

    request_id = Column(String(100), index=True, nullable=True)
    endpoint = Column(String(255), index=True, nullable=True)
    method = Column(String(10), nullable=True)

    user_id = Column(String, ForeignKey("users_v2.id"), nullable=True, index=True)

    # WARNING: Sanitize these before write to prevent token/secret leakage
    system_info = Column(JSON, nullable=False, default=dict)
    request_headers = Column(JSON, nullable=False, default=dict)
    request_payload = Column(JSON, nullable=False, default=dict)

    resolution_notes = Column(Text, nullable=True)


class AuditLog(Base):
    """
    Immutable audit trail for security and compliance.
    
    Records all important actions (create, update, delete) with actor information.
    Never delete rows from this table.
    """
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    actor_id = Column(String, nullable=True, index=True)
    actor_type = Column(String(20), default="user", nullable=False)

    action = Column(String(50), nullable=False, index=True)
    entity_type = Column(String(100), nullable=False, index=True)
    entity_id = Column(String(100), nullable=False, index=True)

    changes_json = Column(JSON, nullable=False, default=dict)
    metadata_json = Column(JSON, nullable=False, default=dict)

    correlation_id = Column(String(100), index=True, nullable=True)


class ActivityFeed(Base):
    """
    User activity feed for in-app notifications and engagement.
    
    Shows user-relevant events like goal achievements, recommendations, etc.
    """
    __tablename__ = "activity_feed"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)

    event_type = Column(String(100), index=True, nullable=True)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)

    icon = Column(String(50), default="default", nullable=False)
    action_link = Column(String(500), nullable=True)

    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), 
                       nullable=False, index=True)

    correlation_id = Column(String(100), index=True, nullable=True)
    metadata_json = Column(JSON, nullable=False, default=dict)

    user = relationship("User", back_populates="activity_feed")


class Notification(Base):
    """
    Multi-channel notification system.
    
    Supports in-app, email, SMS, and push notifications.
    """
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users_v2.id"), index=True, nullable=False)

    channel = Column(String(20), default="in_app", nullable=False)
    status = Column(String(20), default="pending", nullable=False)
    priority = Column(String(20), default="normal", nullable=False)

    subject = Column(String(255), nullable=True)
    body = Column(Text, nullable=True)

    payload_json = Column(JSON, nullable=False, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), 
                       nullable=False, index=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="notifications")
