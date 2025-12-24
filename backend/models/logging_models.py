from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.sql import func
import enum
from datetime import datetime
from .database import Base

class LogLevel(str, enum.Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class BugStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    IGNORED = "IGNORED"

class SystemLog(Base):
    """
    Stores general system logs for auditing and debugging.
    Designed for high-volume writes.
    """
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    level = Column(String, index=True)  # Store enum as string for flexibility
    message = Column(Text, nullable=False)
    module = Column(String, index=True)
    function_name = Column(String, nullable=True)
    line_number = Column(Integer, nullable=True)
    
    # Context
    request_id = Column(String, index=True, nullable=True)
    user_id = Column(Integer, nullable=True) # Optional link to user if authenticated
    
    # Structured Data
    extra_data = Column(JSON, nullable=True)

class BugReport(Base):
    """
    Stores structured bug reports created automatically from unhandled exceptions
    or manually triggered by the system.
    """
    __tablename__ = "bug_reports"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Classification
    error_type = Column(String, index=True) # e.g., ValueError, DatabaseError
    error_message = Column(Text, nullable=False)
    severity = Column(String, default="ERROR") # ERROR, CRITICAL
    status = Column(String, default=BugStatus.OPEN, index=True)
    
    # Technical Details
    stack_trace = Column(Text, nullable=False)
    source_file = Column(String, nullable=True)
    line_number = Column(Integer, nullable=True)
    
    # Context
    request_id = Column(String, index=True, nullable=True)
    endpoint = Column(String, index=True, nullable=True)
    method = Column(String, nullable=True) # GET, POST
    user_id = Column(Integer, nullable=True)
    
    # Environment
    system_info = Column(JSON, nullable=True) # Python version, OS, etc.
    request_headers = Column(JSON, nullable=True) # Safe headers only
    request_payload = Column(JSON, nullable=True) # Request body (sanitized)

    resolution_notes = Column(Text, nullable=True)

class AuditLog(Base):
    """
    Business-level Audit Log.
    Tracks WHO did WHAT to WHICH entity.
    """
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    actor_id = Column(String, nullable=True, index=True) # User ID or System
    actor_type = Column(String, default="user") # user, system, ai
    
    action = Column(String, nullable=False) # CREATE, UPDATE, DELETE, EXECUTE
    entity_type = Column(String, nullable=False, index=True) # Order, Transaction, User
    entity_id = Column(String, nullable=False, index=True)
    
    changes_json = Column(JSON, nullable=True) # Before/After diff or details
    metadata_json = Column(JSON, nullable=True) # Request ID, IP, etc.

import uuid
