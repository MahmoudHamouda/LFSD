"""
SQLAlchemy ORM models for user scores.
"""

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer, Text
from datetime import datetime
from .database import Base

class DBUserScore(Base):
    """
    Model for storing calculated user scores (Financial, Health, Productivity).
    """
    __tablename__ = "user_scores"

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    
    # Main Scores (0-100)
    financial_score = Column(Float, default=0.0)
    health_score = Column(Float, default=0.0)
    productivity_score = Column(Float, default=0.0)
    
    # Financial Breakdown
    savings_rate = Column(Float)
    dti_ratio = Column(Float)
    expense_efficiency = Column(Float)
    financial_cushion = Column(Float)
    
    # Health Breakdown
    activity_score = Column(Float)
    sleep_score = Column(Float)
    nutrition_score = Column(Float)
    consistency_score = Column(Float)
    
    # Productivity Breakdown
    time_freed = Column(Float)
    task_automation = Column(Float)
    life_admin_load = Column(Float)
    
    # Metadata
    meta_json = Column(Text)  # JSON string for diagnostics/extra data
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
