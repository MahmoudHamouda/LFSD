from typing import List, Optional, Any, Dict, Union
from pydantic import BaseModel, Field
from datetime import datetime


class Citation(BaseModel):
    part_index: Optional[int] = None
    content: str
    id: str
    title: Optional[str] = None
    filepath: Optional[str] = None
    url: Optional[str] = None
    metadata: Optional[str] = None
    chunk_id: Optional[str] = None
    reindex_id: Optional[str] = None


class Feedback(BaseModel):
    feedback: str  # Enum in TS, string here for simplicity


class ChatMessage(BaseModel):
    id: str
    role: str
    content: str
    end_turn: Optional[bool] = None
    date: str
    feedback: Optional[str] = None
    context: Optional[str] = None


class Conversation(BaseModel):
    id: str
    title: str
    messages: List[ChatMessage]
    date: str


class ConversationRequest(BaseModel):
    messages: List[ChatMessage]
    conversation_id: Optional[str] = None


class UserInfo(BaseModel):
    access_token: str
    expires_on: str
    id_token: str
    provider_name: str
    user_claims: List[Any]
    user_id: str


class CosmosDBHealth(BaseModel):
    cosmosDB: bool
    status: str


class UI(BaseModel):
    title: str
    chat_title: str
    chat_description: str
    logo: Optional[str] = None
    chat_logo: Optional[str] = None
    show_share_button: Optional[bool] = None
    show_chat_history_button: Optional[bool] = None


class FrontendSettings(BaseModel):
    auth_enabled: Optional[str] = None
    feedback_enabled: Optional[str] = None
    ui: Optional[UI] = None
    sanitize_answer: Optional[bool] = None
    oyd_enabled: Optional[bool] = None


class HistoryListResponse(BaseModel):
    id: str
    title: str
    createdAt: str


class HistoryReadRequest(BaseModel):
    conversation_id: str


class HistoryGenerateRequest(BaseModel):
    messages: List[ChatMessage]
    conversation_id: Optional[str] = None


class HistoryUpdateRequest(BaseModel):
    conversation_id: str
    messages: List[ChatMessage]


class HistoryDeleteRequest(BaseModel):
    conversation_id: str


class HistoryClearRequest(BaseModel):
    conversation_id: str


class HistoryRenameRequest(BaseModel):
    conversation_id: str
    title: str


class MessageFeedbackRequest(BaseModel):
    message_id: str
    message_feedback: str


# Defined here to be shared between Onboarding and User Profile updates
class OnboardingPayload(BaseModel):
    user_id: Optional[str] = None
    # Financial Pillars
    currency: Optional[str] = "USD"
    onboarding_session_id: Optional[str] = None
    session_ids: Optional[List[str]] = []
    is_manual_mode: bool = False

    monthly_income: Optional[float] = 0
    monthly_income_type: Optional[str] = "amount"
    income_frequency: Optional[str] = "Monthly"
    employment_type: Optional[str] = "Full-time"
    other_income_sources: Optional[List[str]] = []

    monthly_expenses: Optional[float] = 0
    monthly_expenses_type: Optional[str] = "amount"

    has_debt: Optional[str] = "no"
    total_debt: Optional[float] = 0
    monthly_debt_payments: Optional[float] = 0

    housing_status: Optional[str] = "rent"
    housing_value: Optional[float] = 0
    rent_amount: Optional[float] = 0
    rent_frequency: Optional[str] = "Monthly"

    car_status: Optional[str] = "no_car"
    car_value: Optional[float] = 0
    car_lease_amount: Optional[float] = 0
    car_lease_frequency: Optional[str] = "Monthly"

    other_assets_status: Optional[str] = "no"
    other_assets_description: Optional[str] = ""

    discretionary_spend: Optional[float] = 0
    discretionary_spend_type: Optional[str] = "amount"

    monthly_bills: Optional[float] = 0
    monthly_bills_type: Optional[str] = "amount"

    monthly_savings: Optional[float] = 0
    monthly_savings_type: Optional[str] = "amount"

    investments_status: Optional[str] = "no"
    investments_value: Optional[float] = 0
    investments_types: Optional[List[str]] = []
    risk_appetite: Optional[str] = "unsure"

    # Health Pillars
    sleep_hours: Optional[str] = "7-8"
    sleep_consistency: Optional[str] = "Mostly"
    wake_tired: Optional[str] = "Sometimes"

    activity_level: Optional[str] = "Moderate"
    activity_type: Optional[str] = "None"

    stress_level: Optional[str] = "Sometimes"
    energy_pattern: Optional[str] = "Stable"

    diet_style: Optional[str] = "Balanced"
    water_intake: Optional[str] = "1-2L"
    smoking_pattern: Optional[str] = "Never"
    alcohol_pattern: Optional[str] = "Occasionally"

    eating_out_frequency: Optional[str] = "Rarely"
    takeaway_frequency: Optional[str] = "Rarely"
    cooking_frequency: Optional[str] = "Rarely"
    nightlife_frequency: Optional[str] = "Rarely"

    # Productivity (Time & Productivity Pillar)
    # A) Work & Structure
    work_status: Optional[str] = "Full-time"
    work_hours_per_week: Optional[str] = "40"
    uses_digital_calendar: Optional[str] = "No"
    commute_duration: Optional[str] = "<15 min"

    # B) Daily Time Use
    time_meals_house_daily: Optional[str] = "1-2 hours"
    time_admin_weekly: Optional[str] = "1-3 hours"

    # C) Time Drains & Style
    main_time_drains: Optional[List[str]] = []
    routine_style: Optional[str] = "I try"
    task_style: Optional[str] = "I react to what's urgent"

    # D) Pressure
    time_overwhelm_level: Optional[str] = "Sometimes"

    # Legacy fields
    services_usage: Optional[int] = 2


class UserIndentityUpdate(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    phoneNumber: Optional[str] = None
    profile: Optional[Dict[str, Any]] = None


class VivPreferencesUpdate(BaseModel):
    riskTolerance: Optional[str] = None
    communicationStyle: Optional[str] = None
    conflictResolutionMode: Optional[str] = None


class UserUpdateRequest(BaseModel):
    identity: Optional[UserIndentityUpdate] = None
    vivPreferences: Optional[VivPreferencesUpdate] = None
    onboarding_data: Optional[OnboardingPayload] = None


class GoalType(str):
    CAR = "car"
    HOUSE = "house"
    EMERGENCY_FUND = "emergency_fund"
    TRAVEL = "travel"
    EDUCATION = "education"
    CUSTOM = "custom"


class GoalBase(BaseModel):
    title: str
    target_amount: float
    target_date: Optional[datetime] = None
    type: str = "custom"
    pillar: str = "finance"
    monthly_contribution_target: float = 0
    priority: str = "medium"


class GoalCreate(GoalBase):
    pass


class GoalUpdate(BaseModel):
    title: Optional[str] = None
    target_amount: Optional[float] = None
    target_date: Optional[datetime] = None
    type: Optional[str] = None
    pillar: Optional[str] = None
    monthly_contribution_target: Optional[float] = None
    priority: Optional[str] = None
    saved_amount: Optional[float] = None


class GoalResponse(GoalBase):
    id: str
    saved_amount: float
    impact_vector_json: Optional[Any] = None


class CoverageResponse(BaseModel):
    category_id: str
    window_days: int
    days_with_data: int
    required_days: int
    coverage_ratio: float
    has_some_data: bool
    no_data: bool
    chart_unlocked: bool
    remaining_days: int
    expected_unlock_date: Optional[str] = None
