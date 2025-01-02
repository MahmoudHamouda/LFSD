from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

# Define the base for models
Base = declarative_base()

class Recommendation(Base):
    """
    Database model for storing user recommendations.
    """
    __tablename__ = "recommendations"

    recommendation_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    type = Column(String(50), nullable=False)  # e.g., "lifestyle", "financial"
    context = Column(String(255), nullable=True)
    content = Column(JSON, nullable=False)  # Recommendation details
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    # Example of optional relationship if `users` table exists
    # user = relationship("User", back_populates="recommendations")
