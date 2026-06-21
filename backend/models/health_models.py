"""
Health Score Models - User health scoring and aggregation.

Canonical model for computed health scores.
"""

import enum
import uuid
from datetime import datetime, timezone, date

from sqlalchemy import (
    Column,
    String,
    Float,
    DateTime,
    ForeignKey,
    JSON,
    Enum,
    Date,
    UniqueConstraint,
    CheckConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


def generate_uuid() -> str:
    """Generate UUID string for primary keys."""
    return str(uuid.uuid4())


class HealthWindow(str, enum.Enum):
    """Time window for health score calculation."""

    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    LAST_90_DAYS = "last_90_days"


class HealthScore(Base):
    """
    Computed health scores (Sleep, Movement, etc.).

    One score per user/window/date.
    """

    __tablename__ = "health_scores"

    __table_args__ = (
        # ✅ Prevent duplicates
        UniqueConstraint(
            "user_id",
            "time_window",
            "score_date",
            name="uq_healthscore_user_window_date",
        ),
        # ✅ Enforce score bounds (0-100)
        CheckConstraint(
            "overall_score >= 0 AND overall_score <= 100",
            name="ck_health_overall_score",
        ),
        CheckConstraint(
            "sleep_score >= 0 AND sleep_score <= 100", name="ck_health_sleep_score"
        ),
        CheckConstraint(
            "movement_score >= 0 AND movement_score <= 100",
            name="ck_health_movement_score",
        ),
        CheckConstraint(
            "recovery_score >= 0 AND recovery_score <= 100",
            name="ck_health_recovery_score",
        ),
        CheckConstraint(
            "nutrition_score >= 0 AND nutrition_score <= 100",
            name="ck_health_nutrition_score",
        ),
        CheckConstraint(
            "lifestyle_score >= 0 AND lifestyle_score <= 100",
            name="ck_health_lifestyle_score",
        ),
        CheckConstraint(
            "confidence >= 0 AND confidence <= 1", name="ck_health_confidence_0_1"
        ),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)

    # ✅ Fixed FK to users_v2
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)

    # ✅ Timezone-aware timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # ✅ Logical date for uniqueness
    score_date = Column(Date, nullable=False, default=date.today, index=True)

    # Scores
    overall_score = Column(Float, default=0.0, nullable=False)
    confidence = Column(Float, default=0.0, nullable=False)  # 0-1

    # Sub-scores
    sleep_score = Column(Float, default=0.0, nullable=False)
    movement_score = Column(Float, default=0.0, nullable=False)
    recovery_score = Column(Float, default=0.0, nullable=False)
    nutrition_score = Column(Float, default=0.0, nullable=False)
    lifestyle_score = Column(Float, default=0.0, nullable=False)

    # ✅ Enum time window
    time_window = Column(
        Enum(HealthWindow), default=HealthWindow.LAST_30_DAYS, nullable=False
    )

    # ✅ JSON column
    data_sources_json = Column(JSON, nullable=False, default=dict)

    user = relationship("User", back_populates="health_scores")
