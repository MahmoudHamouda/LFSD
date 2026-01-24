from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class HealthScore(Base):
    """
    Detailed breakdown of the Health Score (5 Pillars).
    """
    __tablename__ = "health_scores"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    overall_score = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    
    # The 5 Pillars
    sleep_score = Column(Float, default=0.0)
    movement_score = Column(Float, default=0.0)
    recovery_score = Column(Float, default=0.0)
    nutrition_score = Column(Float, default=0.0)
    lifestyle_score = Column(Float, default=0.0)

    # Metadata
    time_window = Column(String, default="last_30_days")
    data_sources_json = Column(JSON, nullable=True) # {"whoop": true, "apple": false}

    user = relationship("User", back_populates="health_scores")
