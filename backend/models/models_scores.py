"""
User Scores Model - Consolidated user scoring system.

WARNING: This table may duplicate VivIndex, FinancialScore, HealthScore, TimeScore.
Consider consolidating to a single canonical scoring system.

Stores computed scores across all pillars (financial, health, time, balance).
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    Float,
    DateTime,
    ForeignKey,
    JSON,
    UniqueConstraint,
    CheckConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


def generate_uuid() -> str:
    """Generate UUID string for primary keys."""
    return str(uuid.uuid4())


class DBUserScore(Base):
    """
    Consolidated user score across all pillars.

    WARNING: This duplicates scoring logic in:
    - VivIndex (models.py)
    - FinancialScore (models.py)
    - HealthScore (health_models.py)
    - TimeScore (models.py)

    TODO: Consolidate to single scoring system.

    One current score per user (uniqueness enforced).
    """

    __tablename__ = "user_scores"

    __table_args__ = (
        # Enforce one current score per user
        UniqueConstraint("user_id", name="uq_user_scores_user_id"),
        # Bounds on pillar scores (0-100)
        CheckConstraint(
            "financial_score >= 0 AND financial_score <= 100",
            name="ck_user_scores_financial_0_100",
        ),
        CheckConstraint(
            "health_score >= 0 AND health_score <= 100",
            name="ck_user_scores_health_0_100",
        ),
        CheckConstraint(
            "time_score >= 0 AND time_score <= 100", name="ck_user_scores_time_0_100"
        ),
        CheckConstraint(
            "balance_score >= 0 AND balance_score <= 100",
            name="ck_user_scores_balance_0_100",
        ),
        CheckConstraint(
            "overall_score >= 0 AND overall_score <= 100",
            name="ck_user_scores_overall_0_100",
        ),
        # Bounds on ratios (0-2 for flexibility, though typically 0-1)
        CheckConstraint(
            "savings_rate >= 0 AND savings_rate <= 2",
            name="ck_user_scores_savings_rate",
        ),
        CheckConstraint("debt_to_income >= 0", name="ck_user_scores_debt_to_income"),
        # Indexes for queries
        Index("ix_user_scores_updated", "updated_at"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)

    # Pillar scores (0-100)
    financial_score = Column(Float, default=0.0, nullable=False)
    health_score = Column(Float, default=0.0, nullable=False)
    time_score = Column(Float, default=0.0, nullable=False)
    balance_score = Column(Float, default=0.0, nullable=False)
    overall_score = Column(Float, default=0.0, nullable=False)

    # Financial components
    savings_rate = Column(Float, default=0.0, nullable=False)
    debt_to_income = Column(Float, default=0.0, nullable=False)
    emergency_fund_months = Column(Float, default=0.0, nullable=False)
    investment_diversity = Column(Float, default=0.0, nullable=False)

    # Health components
    sleep_quality = Column(Float, default=0.0, nullable=False)
    activity_level = Column(Float, default=0.0, nullable=False)
    stress_level = Column(Float, default=0.0, nullable=False)
    nutrition_score = Column(Float, default=0.0, nullable=False)

    # Time components
    productivity_score = Column(Float, default=0.0, nullable=False)
    focus_time_hours = Column(Float, default=0.0, nullable=False)
    meeting_hours = Column(Float, default=0.0, nullable=False)
    work_life_balance = Column(Float, default=0.0, nullable=False)

    # Metadata (proper JSON column)
    meta_json = Column(JSON, nullable=False, default=dict)

    # Timestamps (timezone-aware)
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

    user = relationship("User", back_populates="scores")
