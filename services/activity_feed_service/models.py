from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import declarative_base  # Corrected import for declarative base
import datetime

# Initialize the base for SQLAlchemy models
Base = declarative_base()

class ActivityFeed(Base):
    __tablename__ = "activity_feed"

    activity_id = Column(Integer, primary_key=True, autoincrement=True)  # Ensure primary key auto-increments
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)  # Add nullable=False for consistency
    action_type = Column(String(50), nullable=False)  # Ensure non-nullable
    details = Column(JSON, nullable=False)  # Details about the action, required field
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)  # Non-nullable with default
