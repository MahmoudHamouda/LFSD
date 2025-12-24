from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class NutritionLog(Base):
    """
    Tracks daily nutrition intake.
    """
    __tablename__ = "nutrition_logs"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    
    date = Column(Date, nullable=False, index=True)
    
    calories_in = Column(Integer, nullable=True)
    protein_grams = Column(Float, nullable=True)
    carbs_grams = Column(Float, nullable=True)
    fat_grams = Column(Float, nullable=True)
    
    water_ml = Column(Integer, nullable=True)
    
    source = Column(String, default="manual") # "myfitnesspal", "cronometer"

    user = relationship("User")
