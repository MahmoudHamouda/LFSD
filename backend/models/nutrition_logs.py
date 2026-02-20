"""
Nutrition Logs - Daily nutrition tracking.

Stores user nutrition data from manual entry or third-party integrations
(MyFitnessPal, LoseIt, etc.).
"""

import enum
from datetime import date, datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, ForeignKey, Enum,
    UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class NutritionSource(str, enum.Enum):
    """Sources of nutrition data."""
    MANUAL = "manual"
    MYFITNESSPAL = "myfitnesspal"
    LOSEIT = "loseit"
    CRONOMETER = "cronometer"
    APPLE_HEALTH = "apple_health"


class NutritionLog(Base):
    """
    Daily nutrition logs per user.
    
    One log per (user, date). Stores macros, calories, and water intake.
    """
    __tablename__ = "nutrition_logs"

    __table_args__ = (
        # One log per user per day
        UniqueConstraint("user_id", "date", name="uq_nutrition_user_date"),
        Index("ix_nutrition_user_date", "user_id", "date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)
    
    # The date this log represents
    date = Column(Date, nullable=False, index=True)
    
    # Macros and calories (default to 0 for easier math)
    calories_in = Column(Integer, nullable=False, default=0)
    protein_grams = Column(Float, nullable=False, default=0.0)
    carbs_grams = Column(Float, nullable=False, default=0.0)
    fat_grams = Column(Float, nullable=False, default=0.0)
    
    # Hydration (in liters)
    water_liters = Column(Float, nullable=False, default=0.0)
    
    # Data source
    source = Column(Enum(NutritionSource), default=NutritionSource.MANUAL, nullable=False)
    
    # Audit timestamps (timezone-aware)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), 
                       onupdate=func.now(), nullable=False)
    # Relationship
    user = relationship("User", back_populates="nutrition_logs", foreign_keys=[user_id])
