"""
Health Models - Health integrations, metrics, insights, and user health indexes.

Provides data models for health provider connections (Apple Health, Whoop, etc.),
health metrics storage, computed insights, and user health settings.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Float, DateTime, ForeignKey, JSON, Boolean,
    Enum, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


def generate_uuid() -> str:
    """Generate UUID string for primary keys."""
    return str(uuid.uuid4())


# ============================================================================
# ENUMS
# ============================================================================

class HealthProvider(str, enum.Enum):
    """Supported health data providers."""
    APPLE_HEALTH = "apple_health"
    WHOOP = "whoop"
    FITBIT = "fitbit"
    GARMIN = "garmin"
    OURA = "oura"
    GOOGLE_FIT = "google_fit"


class ConnectionStatus(str, enum.Enum):
    """Health connection lifecycle states."""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    ERROR = "error"


class MetricType(str, enum.Enum):
    """Health metric types."""
    HEART_RATE = "heart_rate"
    HRV = "hrv"
    STEPS = "steps"
    SLEEP_DURATION = "sleep_duration"
    SLEEP_QUALITY = "sleep_quality"
    CALORIES = "calories"
    WORKOUT = "workout"
    WEIGHT = "weight"
    BLOOD_PRESSURE = "blood_pressure"
    OXYGEN_SATURATION = "oxygen_saturation"



class SyncFrequency(str, enum.Enum):
    """Data sync frequency options."""
    REALTIME = "realtime"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"


class TimeWindow(str, enum.Enum):
    """Time windows for index calculation."""
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    LAST_90_DAYS = "last_90_days"
    ALL_TIME = "all_time"


# ============================================================================
# MODELS
# ============================================================================

class DBHealthConnection(Base):
    """
    Health provider OAuth connections.
    
    Stores encrypted credentials and permissions for third-party health data access.
    One connection per (user, provider).
    """
    __tablename__ = "health_connections"

    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_health_conn_user_provider"),
        Index("ix_health_conn_user_status", "user_id", "status"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)
    provider = Column(Enum(HealthProvider), nullable=False, index=True)
    
    # OAuth/API credentials (encrypted at rest)
    # WARNING: Encrypt before storing, decrypt on read
    credentials = Column(String, nullable=False)  # Encrypted JSON blob
    
    # Permissions granted by user (store as JSON for queryability)
    permissions = Column(JSON, nullable=False, default=dict)
    
    status = Column(Enum(ConnectionStatus), default=ConnectionStatus.ACTIVE, nullable=False)
    
    connected_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    metadata_json = Column(JSON, nullable=False, default=dict)

    user = relationship("User", back_populates="health_connections")


class DBHealthMetric(Base):
    """
    Raw health metrics from providers.
    
    Stores time-series health data with optional deduplication by timestamp.
    """
    __tablename__ = "health_metrics"

    __table_args__ = (
        # Optional: Prevent duplicate datapoints from same provider
        # UniqueConstraint("user_id", "provider", "metric_type", "timestamp", 
        #                 name="uq_health_metric_dedupe"),
        Index("ix_health_metrics_user_time", "user_id", "timestamp"),
        Index("ix_health_metrics_user_type_time", "user_id", "metric_type", "timestamp"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)
    provider = Column(Enum(HealthProvider), nullable=False)
    
    metric_type = Column(Enum(MetricType), nullable=False, index=True)
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=True)
    
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Store raw provider data as JSON (not encrypted, for debugging)
    raw_data = Column(JSON, nullable=False, default=dict)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="health_metrics")


class DBUserIndex(Base):
    """
    Computed health index scores per user.
    
    NOTE: This may duplicate VivIndex/HealthScore tables elsewhere.
    Consider consolidating to a single canonical index table.
    """
    __tablename__ = "user_health_indexes"

    __table_args__ = (
        # One index per user per time window
        UniqueConstraint("user_id", "time_window", name="uq_user_index_window"),
        Index("ix_user_index_calculated", "user_id", "calculated_at"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)
    
    # Pillar scores
    financial_index = Column(Float, default=0.0, nullable=False)
    time_index = Column(Float, default=0.0, nullable=False)
    balance_index = Column(Float, default=0.0, nullable=False)
    
    # Metadata

    # Metadata
    time_window = Column(Enum(TimeWindow), default=TimeWindow.LAST_30_DAYS, nullable=False)
    confidence = Column(Float, default=0.0, nullable=False)
    
    calculated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    data_sources = Column(JSON, nullable=False, default=dict)

    user = relationship("User", back_populates="health_indexes")


class DBHealthInsight(Base):
    """
    AI-generated health insights and recommendations.
    
    Personalized insights based on health data patterns.
    """
    __tablename__ = "health_insights"

    __table_args__ = (
        Index("ix_health_insights_user_created", "user_id", "created_at"),
        Index("ix_health_insights_user_dismissed", "user_id", "dismissed_at"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)
    
    title = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    insight_type = Column(String(50), nullable=True, index=True)
    
    # Financial/time impact (store as JSON for structured data)
    financial_impact = Column(JSON, nullable=False, default=dict)
    related_metrics = Column(JSON, nullable=False, default=list)
    
    priority = Column(String(20), default="normal", nullable=False)
    
    is_dismissed = Column(Boolean, default=False, nullable=False)
    dismissed_at = Column(DateTime(timezone=True), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="health_insights")


class DBHealthSettings(Base):
    """
    User health data sync settings per provider.
    
    Controls what data is synced and how frequently.
    """
    __tablename__ = "health_settings"

    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_health_settings_user_provider"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)
    provider = Column(Enum(HealthProvider), nullable=False)
    
    sync_enabled = Column(Boolean, default=True, nullable=False)
    sync_frequency = Column(Enum(SyncFrequency), default=SyncFrequency.DAILY, nullable=False)
    
    # Categories of data to sync (store as JSON array)
    data_categories = Column(JSON, nullable=False, default=list)
    
    last_modified_at = Column(DateTime(timezone=True), server_default=func.now(), 
                             onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="health_settings")
