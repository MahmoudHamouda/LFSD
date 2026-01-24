from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime
import uuid

# Define the base for models
Base = declarative_base()

class Recommendation(Base):
    """
    Database model for storing user recommendations.
    """
    __tablename__ = "recommendations_service_v2"

    recommendation_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False, index=True) 
    type = Column(String(50), nullable=False)  # e.g., "lifestyle", "financial"
    context = Column(String(255), nullable=True)
    content = Column(JSON, nullable=False)  # Recommendation details
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    feedback = relationship("RecommendationFeedback", back_populates="recommendation", cascade="all, delete-orphan")

class RecommendationFeedback(Base):
    """
    Database model for user feedback on specific recommendations.
    """
    __tablename__ = "recommendation_feedback_v2"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    recommendation_id = Column(String, ForeignKey("recommendations_service_v2.recommendation_id"), nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True) 
    rating = Column(Integer, nullable=True) # e.g., 1-5
    is_helpful = Column(Boolean, nullable=True)
    comment = Column(String(1000), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    recommendation = relationship("Recommendation", back_populates="feedback")
