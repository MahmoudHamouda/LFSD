"""
Investment Portfolios - Tracking user financial assets.

Stores manual or synced investment portfolios with performance metrics.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    DateTime,
    ForeignKey,
    JSON,
    UniqueConstraint,
    Numeric,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


def generate_uuid() -> str:
    """Generate UUID string for primary keys."""
    return str(uuid.uuid4())


class InvestmentPortfolio(Base):
    """
    User investment portfolio.

    Tracks value, returns, and asset allocation.
    """

    __tablename__ = "investment_portfolios"

    __table_args__ = (
        # Prevent duplicate portfolios
        UniqueConstraint(
            "user_id",
            "institution_name",
            "portfolio_name",
            name="uq_portfolio_user_institution_name",
        ),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)

    # ✅ Fixed FK to users_v2
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)

    institution_name = Column(String(100), nullable=False)
    portfolio_name = Column(String(255), nullable=True)

    # ✅ Numeric for money (precision 18, 2 decimal places)
    total_value = Column(Numeric(18, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)

    # Performance metrics
    daily_change_percent = Column(Numeric(7, 4), nullable=True)
    total_return_percent = Column(Numeric(7, 4), nullable=True)

    # Asset allocation (stocks, bonds, crypto, etc.)
    asset_allocation_json = Column(JSON, nullable=False, default=dict)

    # ✅ Timezone-aware timestamp
    last_updated = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        index=True,
    )

    user = relationship("User", back_populates="investment_portfolios")
