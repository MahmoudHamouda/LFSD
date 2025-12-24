"""
Enhanced database models for health integrations and user indexes.

This module extends the existing models.py with new tables for:
- Health connections (WHOOP, Apple Health, Android Health)
- Health metrics (sleep, recovery, activity, HRV, steps)
- User indexes (financial wellbeing, time saved, balance)
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Float, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

# ============================================================================
# Health Connection Model
# ============================================================================

class DBHealthConnection(Base):
    """Health connection model for storing user links to health providers."""
    __tablename__ = "health_connections"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    provider = Column(String, nullable=False)  # "whoop", "apple_health", "android_health"
    status = Column(String, default="not_connected")  # "not_connected", "connecting", "connected", "error", "reconnect"
    credentials = Column(Text)  # Encrypted JSON string with OAuth tokens
    permissions = Column(Text)  # JSON array of granted permissions
    error_message = Column(String, nullable=True)
    connected_at = Column(DateTime, nullable=True)
    last_synced_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# ============================================================================
# Health Metric Model
# ============================================================================

class DBHealthMetric(Base):
    """Health metric model for storing health data from various providers."""
    __tablename__ = "health_metrics"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    provider = Column(String, nullable=False)  # "whoop", "apple_health", "android_health"
    metric_type = Column(String, nullable=False)  # "sleep", "recovery", "activity", "hrv", "steps", "heart_rate"
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    raw_data = Column(Text, nullable=True)  # JSON string with full provider data
    created_at = Column(DateTime, default=datetime.utcnow)

# ============================================================================
# User Index Model
# ============================================================================

class DBUserIndex(Base):
    """User index model for storing calculated wellbeing indexes."""
    __tablename__ = "user_indexes"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    financial_wellbeing = Column(Float, nullable=False)  # 0-100
    time_saved = Column(Float, nullable=False)  # 0-100
    balance_index = Column(Float, nullable=True)  # 0-100 (only if health connected)
    trend_financial = Column(Float, default=0.0)  # +/- percentage
    trend_time_saved = Column(Float, default=0.0)  # +/- percentage
    trend_balance = Column(Float, nullable=True)  # +/- percentage
    calculated_at = Column(DateTime, default=datetime.utcnow)

# ============================================================================
# Health Insight Model
# ============================================================================

class DBHealthInsight(Base):
    """Health insight model for storing AI-generated health-to-finance insights."""
    __tablename__ = "health_insights"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    insight_type = Column(String, nullable=False)  # "recovery_low", "sleep_good", "activity_high", "general"
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=True)
    financial_impact = Column(Text, nullable=True)  # JSON: {category, suggestion}
    related_metrics = Column(Text, nullable=True)  # JSON array of {metricType, value}
    created_at = Column(DateTime, default=datetime.utcnow)
    dismissed_at = Column(DateTime, nullable=True)

# ============================================================================
# Health Integration Settings Model
# ============================================================================

class DBHealthSettings(Base):
    """Health integration settings model for user preferences."""
    __tablename__ = "health_settings"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    provider = Column(String, nullable=False)  # "whoop", "apple_health", "android_health"
    enabled = Column(Boolean, default=True)
    data_categories = Column(Text)  # JSON: {sleep, activity, hrv, steps, heartRate}
    sync_frequency = Column(String, default="hourly")  # "realtime", "hourly", "daily"
    notifications_enabled = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
