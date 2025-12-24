from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class LifestyleEvent(Base):
    """
    Tracks 'Quality Time' events like dining out, concerts, or leisure activities.
    Used for 'Treat Yourself' recommendations.
    """
    __tablename__ = "lifestyle_events"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    
    event_type = Column(String, nullable=False) # "dining", "concert", "sports", "travel"
    title = Column(String, nullable=False) # e.g., "Dinner at Nando's"
    
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    
    location_name = Column(String, nullable=True)
    location_lat = Column(Float, nullable=True)
    location_lon = Column(Float, nullable=True)
    
    cost_estimated = Column(Float, nullable=True)
    currency = Column(String, default="USD")
    
    source = Column(String, nullable=True) # "opentable", "ticketmaster", "manual"
    external_id = Column(String, nullable=True)
    
    metadata_json = Column(JSON, nullable=True) # Menu link, ticket seat, etc.

    user = relationship("User")
