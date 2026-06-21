from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base
from .models import generate_uuid

# ============================================================================
# 6. Growth & Monetization Layer
# ============================================================================


class Subscription(Base):
    __tablename__ = "subscriptions"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)

    plan_id = Column(String, nullable=False, default="tier_free")  # tier_free, tier_pro
    status = Column(
        String, nullable=False, default="active"
    )  # active, canceled, past_due, trialing

    current_period_start = Column(DateTime, default=datetime.utcnow)
    current_period_end = Column(DateTime, nullable=True)

    cancel_at_period_end = Column(Boolean, default=False)
    canceled_at = Column(DateTime, nullable=True)

    # External Payment Provider Info (Stripe, etc.)
    provider = Column(String, nullable=True)  # stripe, apple, google
    provider_subscription_id = Column(String, nullable=True, index=True)
    provider_customer_id = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="subscription")


class TierConfig(Base):
    """
    Global configuration for subscription tiers.
    """

    __tablename__ = "tier_configs"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True, default=generate_uuid)
    plan_id = Column(
        String, unique=True, nullable=False, index=True
    )  # tier_free, tier_pro

    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    # Store dynamic limits and features as JSON
    # Example: {"goals": 5, "history_months": 3, "ai_queries_per_day": 5}
    config_json = Column(JSON, nullable=False, default=dict)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserLimitOverride(Base):
    """
    Per-user overrides for plan limits.
    """

    __tablename__ = "user_limit_overrides"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)

    # Example: {"ai_queries_per_day": 50} - overrides the tier limit
    overrides_json = Column(JSON, nullable=False, default=dict)

    reason = Column(String, nullable=True)
    expiration_date = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="limit_overrides")
