from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer, Text, Boolean, JSON
from datetime import datetime
from .database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class BackgroundJob(Base):
    """
    Persisted background job state for async tasks.
    Replaces in-memory JobManager dict.
    """
    __tablename__ = "background_jobs"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, default=generate_uuid)
    
    # Metadata
    user_id = Column(String, nullable=True, index=True) # Optional link to user
    job_type = Column(String, nullable=False) # e.g. "finance_sync", "pdf_parse"
    source = Column(String, default="system")
    
    # State
    status = Column(String, default="pending", index=True) # pending, processing, completed, failed
    progress = Column(Integer, default=0) # 0-100
    
    # Results
    result_json = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True) # TTL support

