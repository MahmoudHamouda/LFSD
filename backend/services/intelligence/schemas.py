"""
Canonical Schemas for the HELM Intelligence Pipeline.

Every pipeline stage communicates via these typed, versioned schemas.
These are the contracts between stages — change them with care.

Design Principles:
    - Deterministic before probabilistic
    - Structured before unstructured
    - Every field is auditable and traceable
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ============================================================================
# Enums
# ============================================================================


class RequestTier(int, Enum):
    """Cost tier classification for LLM routing."""

    TIER_0 = 0  # Fully deterministic — no LLM calls
    TIER_1 = 1  # Single lightweight LLM call (intent OR response)
    TIER_2 = 2  # Dual lightweight LLM calls (intent AND response)
    TIER_3 = 3  # Heavy reasoning (Sonnet/Opus-class + lightweight)


class Dimension(str, Enum):
    """The three pillars of HELM scoring."""

    WEALTH = "wealth"
    HEALTH = "health"
    TIME = "time"


class ActionType(str, Enum):
    """Types of actions the pipeline can dispatch."""

    RESPOND_ONLY = "respond_only"  # Just reply, no side-effects
    EXECUTE_FINANCIAL = "execute_financial"  # Dispatch to financial service
    EXECUTE_CALENDAR = "execute_calendar"  # Dispatch to calendar service
    EXECUTE_MOBILITY = "execute_mobility"  # Dispatch to mobility service
    EXECUTE_HEALTH = "execute_health"  # Dispatch to health service
    EXECUTE_PARTNER = "execute_partner"  # Dispatch to partner integration
    FLAG_FOR_REVIEW = "flag_for_review"  # Human review needed
    QUEUE_DEFERRED = "queue_deferred"  # Queue for later execution


# ============================================================================
# Stage 1 Output: InputEnvelope
# ============================================================================


class InputEnvelope(BaseModel):
    """
    Normalized, sanitized user input with session metadata.
    Produced by Stage 1 (Input Processing). No LLM involved.
    """

    # Identity
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Content
    raw_text: str
    normalized_text: str  # Stripped, lowered, sanitized
    attachments: List[Dict[str, Any]] = Field(default_factory=list)

    # Session Context
    session_id: Optional[str] = None
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    device_type: Optional[str] = None
    locale: str = "en"
    # Browser-provided coordinates for the current request, e.g.
    # {"lat": 25.2, "lng": 55.27}. Present only when the client shares location.
    location: Optional[Dict[str, float]] = None

    class Config:
        use_enum_values = True


# ============================================================================
# Stage 2 Output: ContextFrame
# ============================================================================


class HelmScores(BaseModel):
    """Current HELM tri-dimensional scores."""

    wealth: float = 50.0
    health: float = 50.0
    time: float = 50.0


class FinancialSnapshot(BaseModel):
    """Compressed financial context (~50 tokens)."""

    total_balance: float = 0.0
    monthly_income: float = 0.0
    monthly_expenses: float = 0.0
    monthly_savings: float = 0.0
    total_debt: float = 0.0
    emergency_fund_months: float = 0.0
    currency: str = "AED"


class HealthBaseline(BaseModel):
    """Compressed health context (~40 tokens)."""

    sleep_hours_avg: float = 7.0
    sleep_quality: float = 50.0
    activity_level: float = 50.0
    hrv_avg: Optional[float] = None
    stress_level: float = 50.0
    steps_avg: int = 5000


class TimeBaseline(BaseModel):
    """Compressed time/productivity context (~30 tokens)."""

    focus_hours_daily: float = 4.0
    meeting_hours_daily: float = 2.0
    commute_minutes: int = 30
    work_life_balance: float = 50.0
    productivity_score: float = 50.0


class ContextFrame(BaseModel):
    """
    Complete user context assembled from multiple data sources.
    Produced by Stage 2 (Context Assembly). No LLM involved.

    Target: ~200 tokens when serialized for LLM consumption.
    Versioned for backward compatibility.
    """

    schema_version: str = "1.0"

    # User Profile
    user_id: str
    user_name: str = "User"
    user_email: Optional[str] = None

    # Current Scores
    helm_scores: HelmScores = Field(default_factory=HelmScores)

    # Domain Snapshots (compressed)
    financial: FinancialSnapshot = Field(default_factory=FinancialSnapshot)
    health: HealthBaseline = Field(default_factory=HealthBaseline)
    time: TimeBaseline = Field(default_factory=TimeBaseline)

    # Goals
    life_goals: List[Dict[str, Any]] = Field(default_factory=list)

    # Memory: verified recurring commitments (subscriptions/bills), e.g.
    # [{"name": "Careem Plus", "amount": 49.0, "cadence": "monthly"}]. Used by
    # the decision engine to ground recommendations ("you already pay for X").
    commitments: List[Dict[str, Any]] = Field(default_factory=list)

    # Preferences
    risk_tolerance: str = "medium"  # low, medium, high
    trade_off_rule: str = "balanced_living"

    # State Flags
    crisis_mode: bool = False
    crisis_dimensions: List[str] = Field(default_factory=list)

    # Confidence in data freshness
    data_confidence: Dict[str, float] = Field(
        default_factory=lambda: {"wealth": 0.5, "health": 0.5, "time": 0.5}
    )

    class Config:
        use_enum_values = True


# ============================================================================
# Stage 3 Output: IntentResult
# ============================================================================


class IntentResult(BaseModel):
    """
    Classified intent with confidence and extracted entities.
    Produced by Stage 3 (Intent Classification).
    Deterministic-first, LLM fallback for ambiguous inputs.
    """

    intent: str  # From IntentTaxonomy (e.g., "balance_check", "career_change")
    confidence: float = 1.0  # 0.0 – 1.0
    dimensions: List[str] = Field(
        default_factory=list
    )  # e.g., ["wealth"], ["health", "time"]
    tier: RequestTier = RequestTier.TIER_0

    # Extracted entities
    entities: Dict[str, Any] = Field(default_factory=dict)

    # Classification metadata
    classified_by: str = "deterministic"  # "deterministic" or "llm"
    original_text: str = ""
    llm_tokens_used: int = 0

    # Compact, resolved view of the recent conversation (last substantive
    # assistant turn + recent user turns). Threaded to later stages so response
    # generation can resolve referents ("some", "them", "those") and stay on
    # topic. Kept short (~a few hundred chars) to bound token cost.
    conversation_context: str = ""

    # Browser-provided coordinates for this request (if shared). Used by
    # location-aware intents such as local_search to return real nearby places.
    request_location: Optional[Dict[str, float]] = None

    class Config:
        use_enum_values = True


# ============================================================================
# Stage 4 Output: ScoreDeltas
# ============================================================================


class DimensionDelta(BaseModel):
    """Score impact for a single dimension."""

    dimension: str  # "wealth", "health", or "time"
    delta: float = 0.0  # [-100, +100]
    direction: str = "neutral"  # "up", "down", "neutral"
    policy_rule: str = ""  # Which rule produced this delta
    reasoning: str = ""  # Human-readable explanation
    temporal_weight: str = "short_term"  # "short_term" or "long_term"


class ScoreDeltas(BaseModel):
    """
    Tri-dimensional impact scores computed by deterministic policy rules.
    Produced by Stage 4 (Score Evaluation Engine). No LLM involved.

    Every delta traces back to a specific policy rule and input.
    """

    wealth: DimensionDelta = Field(
        default_factory=lambda: DimensionDelta(dimension="wealth")
    )
    health: DimensionDelta = Field(
        default_factory=lambda: DimensionDelta(dimension="health")
    )
    time: DimensionDelta = Field(
        default_factory=lambda: DimensionDelta(dimension="time")
    )

    # Aggregate assessment
    net_impact: str = "neutral"  # "positive", "negative", "neutral", "mixed"
    has_tradeoff: bool = False  # True if dimensions conflict
    crisis_override: bool = False

    # Goal impact
    goal_impacts: List[str] = Field(default_factory=list)

    # Policy metadata
    policies_applied: List[str] = Field(default_factory=list)

    class Config:
        use_enum_values = True


# ============================================================================
# Stage 5 Output: ActionPlan
# ============================================================================


class ActionStep(BaseModel):
    """A single action to execute."""

    action_type: ActionType = ActionType.RESPOND_ONLY
    target_service: Optional[str] = None  # e.g., "finance_service", "calendar_service"
    parameters: Dict[str, Any] = Field(default_factory=dict)
    requires_confirmation: bool = False
    idempotency_key: Optional[str] = None


class ActionPlan(BaseModel):
    """
    Recommended action(s) based on intent + score evaluation.
    Produced by Stage 5 (Decision Synthesis).

    For most requests, this is a template lookup.
    For novel scenarios, heavy LLM produces it.
    """

    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Actions to execute
    steps: List[ActionStep] = Field(default_factory=list)

    # Response configuration
    response_template_id: Optional[str] = None  # For Tier 0 template responses
    response_tone: str = "warm_direct"  # HELM's persona

    # Synthesis metadata
    synthesized_by: str = "template"  # "template" or "llm"
    llm_tokens_used: int = 0
    escalation_reason: Optional[str] = None  # Why heavy LLM was called

    class Config:
        use_enum_values = True


# ============================================================================
# Stage 6 Output: ResponseEnvelope
# ============================================================================


class ResponseEnvelope(BaseModel):
    """
    Final user-facing response.
    Produced by Stage 6 (Response Generation).
    """

    text: str = ""
    response_type: str = "text"  # "text", "financial_report", "mobility_options", etc.
    data: Dict[str, Any] = Field(default_factory=dict)

    # Generation metadata
    generated_by: str = "template"  # "template" or "llm"
    llm_tokens_used: int = 0
    template_id: Optional[str] = None

    class Config:
        use_enum_values = True


# ============================================================================
# Stage 7 Output: PipelineTrace
# ============================================================================


class CostSummary(BaseModel):
    """Per-request cost tracking."""

    tier: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    budget_exceeded: bool = False
    stages: Dict[str, Dict[str, int]] = Field(default_factory=dict)


class StageTimings(BaseModel):
    """Latency measurements for each pipeline stage."""

    input_processing_ms: float = 0.0
    context_assembly_ms: float = 0.0
    intent_classification_ms: float = 0.0
    score_evaluation_ms: float = 0.0
    tradeoff_validation_ms: float = 0.0
    decision_synthesis_ms: float = 0.0
    response_generation_ms: float = 0.0
    execution_logging_ms: float = 0.0
    total_ms: float = 0.0


class PipelineTrace(BaseModel):
    """
    Complete audit record for a single pipeline execution.
    Written synchronously before response is returned.
    Append-only, immutable, queryable.

    This is the source of truth for compliance, debugging, and the learning loop.
    """

    # Identity
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str = ""
    user_id: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Tier classification
    tier: int = 0

    # Stage outputs (serialized snapshots)
    input_envelope: Optional[Dict[str, Any]] = None
    context_frame: Optional[Dict[str, Any]] = None
    intent_result: Optional[Dict[str, Any]] = None
    score_deltas: Optional[Dict[str, Any]] = None
    action_plan: Optional[Dict[str, Any]] = None
    response_envelope: Optional[Dict[str, Any]] = None

    # Token accounting
    total_input_tokens: int = 0
    total_output_tokens: int = 0

    # Performance
    timings: StageTimings = Field(default_factory=StageTimings)

    # Execution result
    execution_success: bool = True
    error_message: Optional[str] = None

    # Phase 2: Cost & tradeoff
    cost_summary: Optional[Dict[str, Any]] = None
    tradeoff_resolution: Optional[str] = None  # proceed/clarify/escalate/safe_minimal

    class Config:
        use_enum_values = True


# ============================================================================
# Pipeline Result (returned to caller)
# ============================================================================


class PipelineResult(BaseModel):
    """Top-level result from IntelligencePipeline.process()."""

    response: ResponseEnvelope
    trace: PipelineTrace
    tier: int = 0
    tradeoff_resolution: Optional[str] = None

    class Config:
        use_enum_values = True
