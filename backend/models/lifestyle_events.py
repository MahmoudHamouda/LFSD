"""
Lifestyle Events - Tracking dining, events, and leisure.

Stores structured lifestyle data for balance scoring and analytics.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    JSON,
    Numeric,
    Float,
    Enum,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


def generate_uuid() -> str:
    """Generate UUID string for primary keys."""
    return str(uuid.uuid4())


class LifestyleEventType(str, enum.Enum):
    """Types of lifestyle events."""

    DINING = "dining"
    CONCERT = "concert"
    SPORTS = "sports"
    TRAVEL = "travel"
    LEISURE = "leisure"


class LifestyleEvent(Base):
    """
    User lifestyle event.
    """

    __tablename__ = "lifestyle_events"

    __table_args__ = (
        # Prevent duplicate ingestion
        UniqueConstraint(
            "user_id", "source", "external_id", name="uq_lifestyle_source_external"
        ),
        Index("ix_lifestyle_user_time", "user_id", "start_time"),
        Index("ix_lifestyle_user_type", "user_id", "event_type"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)

    # ✅ Fixed FK to users_v2
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)

    # ✅ Enum event type
    event_type = Column(Enum(LifestyleEventType), nullable=False)
    title = Column(String(255), nullable=False)

    # ✅ Timezone-aware timestamps
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=True)

    location_name = Column(String(255), nullable=True)
    location_lat = Column(Float, nullable=True)
    location_lon = Column(Float, nullable=True)

    # ✅ Numeric for money
    cost_estimated = Column(Numeric(18, 2), nullable=True)
    currency = Column(String(3), default="USD", nullable=False)

    source = Column(String(50), nullable=True)
    external_id = Column(String(255), nullable=True)

    metadata_json = Column(JSON, nullable=False, default=dict)

    # Audit timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        index=True,
    )

    user = relationship("User", back_populates="lifestyle_events")
