"""
Enterprise-Grade Database Models for Viv Logic Engine.
"""

from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer, Text, Boolean, Date, JSON, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

# ============================================================================
# 1. Core User & Logic Layer
# ============================================================================

class User(Base):
    __tablename__ = "users_v2"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    auth0_id = Column(String, unique=True, index=True, nullable=True)  # Auth0 user ID
    hashed_password = Column(String, nullable=True)  # Now optional for Auth0 users
    profile_json = Column(JSON, nullable=True)  # Unstructured bio data
    viv_preferences = Column(JSON, nullable=True)  # Risk tolerance, comm style, etc.
    
    # Account Status
    account_status = Column(String, default="ACTIVE") # ACTIVE, LOCKED
    role = Column(String, default="user") # user, admin
    
    # Onboarding State Machine
    onboarding_status = Column(String, default="NOT_STARTED") # NOT_STARTED, IN_PROGRESS, COMPLETE
    onboarding_step = Column(String, nullable=True)
    onboarding_version = Column(Integer, default=1)
    
    # Password Reset
    password_reset_token = Column(String, nullable=True, index=True)
    password_reset_expires = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    viv_indexes = relationship("VivIndex", back_populates="user", cascade="all, delete-orphan")
    life_goals = relationship("LifeGoal", back_populates="user", cascade="all, delete-orphan")
    financial_accounts = relationship("FinancialAccount", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("FinancialTransaction", back_populates="user", cascade="all, delete-orphan")
    health_daily_summaries = relationship("HealthDailySummary", back_populates="user", cascade="all, delete-orphan")
    sleep_sessions = relationship("SleepSession", back_populates="user", cascade="all, delete-orphan")
    workouts = relationship("Workout", back_populates="user", cascade="all, delete-orphan")
    calendar_events = relationship("CalendarEvent", back_populates="user", cascade="all, delete-orphan")
    mobility_trips = relationship("MobilityTrip", back_populates="user", cascade="all, delete-orphan")
    viv_logs = relationship("VivLog", back_populates="user", cascade="all, delete-orphan")
    connections = relationship("Connection", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    limit_overrides = relationship("UserLimitOverride", back_populates="user", cascade="all, delete-orphan")
    statements = relationship("Statement", back_populates="user", cascade="all, delete-orphan")
    financial_scores = relationship("FinancialScore", back_populates="user", cascade="all, delete-orphan")
    time_scores = relationship("TimeScore", back_populates="user", cascade="all, delete-orphan")
    health_data_samples = relationship("HealthDataSample", back_populates="user", cascade="all, delete-orphan")
    subscription = relationship("Subscription", uselist=False, back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("DBConversation", back_populates="user", cascade="all, delete-orphan")


class Connection(Base):
    """Stores OAuth credentials and status for external providers."""
    __tablename__ = "connections"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)
    
    provider = Column(String, nullable=False) # uber, whoop, google, etc.
    status = Column(String, default="disconnected")
    credentials_json = Column(Text, nullable=True) # Encrypted JSON string
    metadata_json = Column(Text, nullable=True) # Extra info like permissions, scopes
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # OAuth Token Storage
    access_token = Column(String, nullable=True)
    refresh_token = Column(String, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    token_type = Column(String, nullable=True)
    scope = Column(String, nullable=True)

    user = relationship("User", back_populates="connections")

class HealthDataSample(Base):
    """Normalized health data from external providers."""
    __tablename__ = "health_data_samples"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)
    
    source = Column(String, nullable=False) # "google_fit" | "apple_health"
    date = Column(DateTime, nullable=False, index=True)
    
    steps = Column(Integer, nullable=True)
    distance_m = Column(Float, nullable=True)
    active_minutes = Column(Integer, nullable=True)
    calories_kcal = Column(Float, nullable=True)
    resting_hr_bpm = Column(Integer, nullable=True)
    avg_hr_bpm = Column(Integer, nullable=True)
    sleep_minutes = Column(Integer, nullable=True)
    
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="health_data_samples")


class VivIndex(Base):
    """Time-series tracking of the 3 tenants."""
    __tablename__ = "viv_indexes"
    __table_args__ = (
        Index('idx_viv_index_user_timestamp', 'user_id', 'timestamp'),
        {'extend_existing': True}
    )

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    financial_score = Column(Float, default=50.0) # 0-100
    health_score = Column(Float, default=50.0)    # 0-100
    time_score = Column(Float, default=50.0)      # 0-100
    confidence = Column(Float, default=1.0)       # 0.0-1.0 (New: Fix for Silent Average)
    
    snapshot_reason = Column(Text, nullable=True) # e.g., "Large purchase detected"

    user = relationship("User", back_populates="viv_indexes")


class LifeGoal(Base):
    """Crucial for decision making."""
    __tablename__ = "life_goals_v2"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)
    
    title = Column(String, nullable=False)
    target_amount = Column(Float, nullable=False)
    saved_amount = Column(Float, default=0.0)
    target_date = Column(DateTime, nullable=True) # Renamed from deadline for consistency
    
    type = Column(String, nullable=True) # car, house, emergency_fund, travel, education, custom
    pillar = Column(String, default="finance") # finance, time, health
    monthly_contribution_target = Column(Float, default=0.0)
    
    impact_vector_json = Column(JSON, nullable=True) # {"finance": -100, "health": +20}
    priority = Column(String, default="medium") # "high", "medium", "low"

    user = relationship("User", back_populates="life_goals")


# ============================================================================
# 2. Deep Finance (The "Wealth" Tenant)
# ============================================================================

class FinancialAccount(Base):
    __tablename__ = "financial_accounts_v2"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)
    
    institution_name = Column(String, nullable=False)
    account_type = Column(String, nullable=False) # checking, savings, credit
    current_balance = Column(Float, default=0.0)
    limit = Column(Float, nullable=True)

    user = relationship("User", back_populates="financial_accounts")
    transactions = relationship("FinancialTransaction", back_populates="account", cascade="all, delete-orphan")


from .logging_models import SystemLog, BugReport, LogLevel, BugStatus, ActivityFeed, AuditLog, Notification

__all__ = [
    "User", "Connection", "VivIndex", "LifeGoal", "FinancialAccount", 
    "FinancialTransaction", "HealthDailySummary", "SleepSession", "Workout", 
    "CalendarEvent", "MobilityTrip", "VivLog", "DBConversation", "DBMessage",
    "SystemLog", "BugReport", "Recommendation", "ActivityFeed", "OnboardingSession",
    "Order"
]


class Statement(Base):
    """Stores metadata for uploaded bank statements."""
    __tablename__ = "statements"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=True, index=True)
    
    bank_name = Column(String, nullable=True)
    period_start = Column(Date, nullable=True)
    period_end = Column(Date, nullable=True)
    total_credits = Column(Float, default=0.0)
    total_debits = Column(Float, default=0.0)
    
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="statements")
    transactions = relationship("FinancialTransaction", back_populates="statement", cascade="all, delete-orphan")


class FinancialTransaction(Base):
    """The Deep Dive into spending."""
    __tablename__ = "transactions_v2"
    __table_args__ = (
        Index('idx_transactions_user_date', 'user_id', 'transaction_date'),
        {'extend_existing': True}
    )

    id = Column(String, primary_key=True, default=generate_uuid)
    account_id = Column(String, ForeignKey("financial_accounts_v2.id"), nullable=True, index=True) # Made nullable to allow statement-only transactions initially
    statement_id = Column(String, ForeignKey("statements.id"), nullable=True, index=True) # Link to source statement
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=True, index=True)
    
    amount = Column(Float, nullable=False)
    currency_code = Column(String, default="USD")
    transaction_date = Column(DateTime, default=datetime.utcnow, index=True)
    description = Column(String, nullable=True) # Added description field
    
    merchant_name = Column(String, nullable=True)
    merchant_category_code = Column(String, nullable=True)
    category_primary = Column(String, nullable=True) # e.g., "Food & Drink"
    category_detailed = Column(String, nullable=True) # e.g., "Coffee Shop"
    
    is_recurring = Column(Boolean, default=False)
    location_lat = Column(Float, nullable=True)
    location_lon = Column(Float, nullable=True)
    
    # Governance
    deduplication_key = Column(String, unique=True, index=True, nullable=True)

    user = relationship("User", back_populates="transactions")
    account = relationship("FinancialAccount", back_populates="transactions")
    statement = relationship("Statement", back_populates="transactions")
    order = relationship("Order", back_populates="transaction", uselist=False)


class RecurringBill(Base):
    """Verified recurring commitments."""
    __tablename__ = "recurring_bills"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)
    
    name = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    cadence = Column(String, default="monthly") # monthly, unknown
    next_due_date = Column(Date, nullable=True)
    category = Column(String, nullable=True)
    
    is_verified = Column(Boolean, default=False)
    
    user = relationship("User", back_populates="recurring_bills")


# ============================================================================
# 3. Deep Health (The "Wellbeing" Tenant)
# ============================================================================

class HealthDailySummary(Base):
    __tablename__ = "health_daily_summaries"
    __table_args__ = (
        Index('idx_health_summary_user_date', 'user_id', 'date'),
        {'extend_existing': True}
    )

    id = Column(String, primary_key=True, default=generate_uuid) # Added ID for consistency
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    
    sleep_duration_minutes = Column(Integer, nullable=True)
    sleep_quality_score = Column(Float, nullable=True) # 0-100
    hrv_average = Column(Float, nullable=True)
    resting_heart_rate = Column(Integer, nullable=True)
    steps_count = Column(Integer, nullable=True)

    user = relationship("User", back_populates="health_daily_summaries")


class SleepSession(Base):
    __tablename__ = "sleep_sessions"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)
    
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    
    deep_sleep_minutes = Column(Integer, nullable=True)
    rem_sleep_minutes = Column(Integer, nullable=True)
    wake_count = Column(Integer, nullable=True)

    user = relationship("User", back_populates="sleep_sessions")


class Workout(Base):
    __tablename__ = "workouts"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)
    
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    
    activity_type = Column(String, nullable=False) # Running, Lifting, Yoga
    calories_burned = Column(Integer, nullable=True)
    average_heart_rate = Column(Integer, nullable=True)
    perceived_exertion = Column(Float, nullable=True) # 0-10 scale

    user = relationship("User", back_populates="workouts")


# ============================================================================
# 4. Deep Time & Mobility (The "Productivity" Tenant)
# ============================================================================

class CalendarEvent(Base):
    __tablename__ = "calendar_events"
    __table_args__ = (
        Index('idx_calendar_events_user_start', 'user_id', 'start_time'),
        {'extend_existing': True}
    )

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)
    
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False)
    
    title = Column(String, nullable=True) # hashed/sanitized
    is_meeting = Column(Boolean, default=False)
    attendee_count = Column(Integer, default=0)
    location_context = Column(String, nullable=True) # "wfh" | "office" | "traveling"

    user = relationship("User", back_populates="calendar_events")


class MobilityTrip(Base):
    __tablename__ = "mobility_trips"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)
    
    provider = Column(String, nullable=False) # Uber/Lyft
    pickup_time = Column(DateTime, nullable=True)
    dropoff_time = Column(DateTime, nullable=True)
    
    cost_amount = Column(Float, nullable=True)
    currency = Column(String, default="USD")
    trip_type = Column(String, nullable=True) # "economy" | "premium"
    
    origin_lat = Column(Float, nullable=True)
    origin_lon = Column(Float, nullable=True)
    destination_lat = Column(Float, nullable=True)
    destination_lon = Column(Float, nullable=True)

    user = relationship("User", back_populates="mobility_trips")


# ============================================================================
# 5. Intelligence Layer (The Audit Trail)
# ============================================================================

class VivLog(Base):
    """Tracks WHY Viv gave specific advice."""
    __tablename__ = "viv_logs"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    user_intent = Column(String, nullable=True) # e.g., "order_sushi"
    context_snapshot_json = Column(JSON, nullable=True) # Values of Finance/Health/Time at decision
    decision_logic = Column(Text, nullable=True) # e.g., "Approved because Health < 30"
    ai_response = Column(Text, nullable=True)

    user = relationship("User", back_populates="viv_logs")


class Recommendation(Base):
    __tablename__ = "recommendations"
    __table_args__ = {'extend_existing': True}
    
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    
    type = Column(String, nullable=False) # "mobility.car_purchase"
    source = Column(String, default="auto") # "auto", "manual"
    
    content_json = Column(JSON, nullable=False) # Full structured response
    status = Column(String, default="active") # active, dismissed, acted_upon
    
    user = relationship("User", back_populates="recommendations")




# ============================================================================
# 5. Chat & Conversation Models
# ============================================================================

class DBConversation(Base):
    __tablename__ = "conversations"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=True, index=True) # Optional for now, but suggested for usage tracking
    title = Column(String, nullable=True)
    date = Column(DateTime, default=datetime.utcnow)
    
    messages = relationship("DBMessage", back_populates="conversation", cascade="all, delete-orphan")
    user = relationship("User", back_populates="conversations")

class DBMessage(Base):
    __tablename__ = "messages"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, default=generate_uuid)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=True, index=True) # Tracking which user sent it (or system)
    role = Column(String, nullable=False) # "user", "assistant", "system"
    content = Column(Text, nullable=False)
    date = Column(DateTime, default=datetime.utcnow)
    feedback = Column(String, nullable=True) # "positive", "negative", etc.
    
    # Token Tracking (Growth Agent)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    model_used = Column(String, nullable=True)

    conversation = relationship("DBConversation", back_populates="messages")
    user = relationship("User")

# Aliases for backward compatibility with history_routes
DBTransaction = FinancialTransaction
DBFinancial = FinancialAccount
DBActivity = Workout
# Placeholders for missing models to prevent ImportErrors
class Order(Base):
    """
    Represents a concrete request for goods or services (e.g., a ride, a food order).
    Acts as the 'Truth' for external actions.
    """
    __tablename__ = "orders"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)
    transaction_id = Column(String, ForeignKey("transactions_v2.id"), nullable=True) # Linked financial record
    
    # Core Data
    provider = Column(String, nullable=False) # uber, careem, etc.
    service_type = Column(String, nullable=False) # mobility, food, etc.
    status = Column(String, default="PENDING", index=True) # PENDING, CONFIRMED, FAILED, COMPLETED, CANCELLED
    
    # Financials
    amount_estimated = Column(Float, nullable=True)
    amount_final = Column(Float, nullable=True)
    currency = Column(String, default="AED")
    
    # External Linkage
    external_order_id = Column(String, nullable=True, index=True) # Uber's ride_id
    idempotency_key = Column(String, unique=True, index=True, nullable=True) # For de-duplication
    
    # Metadata
    details_json = Column(JSON, nullable=True) # Full payload: start/end lat, driver info, etc.
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User")
    transaction = relationship("FinancialTransaction", back_populates="order")

# Alias for backward compatibility if needed, but we prefer Order
DBOrder = Order

class DBNotification(Base):
    __tablename__ = "notifications"
    __table_args__ = {'extend_existing': True}
    id = Column(String, primary_key=True, default=generate_uuid)


class OnboardingSession(Base):
    """Temporary storage for onboarding data before user creation."""
    __tablename__ = "onboarding_sessions"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, default=generate_uuid)
    data_json = Column(JSON, nullable=True) # Stores parsed statement data, income, etc.
    created_at = Column(DateTime, default=datetime.utcnow)


class FinancialScore(Base):
    """
    Detailed breakdown of the Financial Wellbeing Score (8 Pillars).
    """
    __tablename__ = "financial_scores"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    overall_score = Column(Float, default=0.0)
    
    # The 8 Pillars (New Categorization)
    cashflow_stability_score = Column(Float, default=0.0)
    bills_coverage_score = Column(Float, default=0.0)
    discretionary_control_score = Column(Float, default=0.0)
    savings_rate_score = Column(Float, default=0.0)
    emergency_buffer_score = Column(Float, default=0.0)
    debt_load_score = Column(Float, default=0.0)
    networth_momentum_score = Column(Float, default=0.0)
    investment_health_score = Column(Float, default=0.0)

    # Metadata
    time_window = Column(String, default="last_3_months")
    data_sources_json = Column(JSON, nullable=True) # {"statements": true, "onboarding": true}

    # Snapshot Totals (For Dashboard Flow)
    total_monthly_income = Column(Float, default=0.0)
    total_monthly_expenses = Column(Float, default=0.0) # Discretionary
    total_monthly_bills = Column(Float, default=0.0)    # Fixed
    total_monthly_savings = Column(Float, default=0.0)
    total_assets_value = Column(Float, default=0.0)

    user = relationship("User", back_populates="financial_scores")


class TimeScore(Base):
    """
    Detailed breakdown of the Time Management Score (7 Pillars).
    """
    __tablename__ = "time_scores_v2"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    overall_score = Column(Float, default=0.0)
    
    # The 7 Time Pillars
    schedule_coverage_score = Column(Float, default=0.0)  # % of day with scheduled events
    planning_habit_score = Column(Float, default=0.0)     # consistency of planning ahead
    focus_blocks_score = Column(Float, default=0.0)       # presence of uninterrupted work time
    meeting_load_score = Column(Float, default=0.0)       # % of time in meetings (inverse)
    context_switching_score = Column(Float, default=0.0)  # frequency of task changes (inverse)
    weekly_rhythm_score = Column(Float, default=0.0)      # consistency week-to-week
    time_alignment_score = Column(Float, default=0.0)     # events aligned with priorities

    # Metadata
    time_window = Column(String, default="last_30_days")
    data_sources_json = Column(JSON, nullable=True)  # {"calendar": true, "manual": true}

    # Snapshot Metrics
    total_scheduled_hours = Column(Float, default=0.0)
    total_meeting_hours = Column(Float, default=0.0)
    total_focus_hours = Column(Float, default=0.0)
    avg_events_per_day = Column(Float, default=0.0)

    user = relationship("User", back_populates="time_scores")


class FeatureInterest(Base):
    """Tracks user interest in upcoming features."""
    __tablename__ = "feature_interests"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)
    
    feature_name = Column(String, nullable=False) # e.g., "whoop_integration", "apple_health"
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="feature_interests")

User.feature_interests = relationship("FeatureInterest", back_populates="user", cascade="all, delete-orphan")


class HealthProfile(Base):
    """Stores persistent health attributes and habits."""
    __tablename__ = "health_profiles"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)
    
    diet_style = Column(String, nullable=True) # e.g., "Mediterranean", "Balanced"
    water_intake_range = Column(String, nullable=True) # "1-2L"
    smoking_pattern = Column(String, nullable=True)
    alcohol_pattern = Column(String, nullable=True)
    stress_level = Column(String, nullable=True) # "Sometimes", "Often"
    energy_pattern = Column(String, nullable=True) # "Stable", "Crash"
    activity_self_report = Column(String, nullable=True) # "Moderate"
    
    lifestyle_habits_json = Column(JSON, nullable=True) # {"eating_out": "Rarely", ...}
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="health_profile")

User.health_profile = relationship("HealthProfile", uselist=False, back_populates="user", cascade="all, delete-orphan")


class TimeProfile(Base):
    """Manual inputs for Time & Productivity."""
    __tablename__ = "time_profiles"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)

    # A) Work & Structure
    work_status = Column(String, nullable=True) # Full-time, Part-time, etc.
    work_hours_per_week = Column(String, nullable=True) # <20, 20-35, etc.
    uses_digital_calendar = Column(String, nullable=True) # Yes - Google, etc.
    commute_duration = Column(String, nullable=True) # <15 min, etc.

    # B) Daily Time Use
    time_meals_house_daily = Column(String, nullable=True)
    time_admin_weekly = Column(String, nullable=True)

    # C) Time Drains & Style
    main_time_drains = Column(JSON, nullable=True) # List of strings
    routine_style = Column(String, nullable=True)
    task_style = Column(String, nullable=True)

    # D) Pressure
    time_overwhelm_level = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="time_profile")


class TimeEvent(Base):
    """Normalized calendar events."""
    __tablename__ = "time_events"
    __table_args__ = {'extend_existing': True}

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)
    
    source = Column(String, nullable=False) # google_calendar, screenshot, manual
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=True)
    
    title = Column(String, nullable=True)
    location = Column(String, nullable=True)
    is_all_day = Column(Boolean, default=False)
    category = Column(String, nullable=True) # Work, Personal, Commute, Admin, Unknown
    
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="time_events")


# Add relationships to User
User.feature_interests = relationship("FeatureInterest", back_populates="user", cascade="all, delete-orphan")
User.health_profile = relationship("HealthProfile", uselist=False, back_populates="user", cascade="all, delete-orphan")
User.time_profile = relationship("TimeProfile", uselist=False, back_populates="user", cascade="all, delete-orphan")
User.time_events = relationship("TimeEvent", back_populates="user", cascade="all, delete-orphan")
User.time_scores = relationship("TimeScore", back_populates="user", cascade="all, delete-orphan")
User.recurring_bills = relationship("RecurringBill", back_populates="user", cascade="all, delete-orphan")
User.recommendations = relationship("Recommendation", back_populates="user", cascade="all, delete-orphan")
User.activity_feed = relationship("ActivityFeed", back_populates="user", cascade="all, delete-orphan")
