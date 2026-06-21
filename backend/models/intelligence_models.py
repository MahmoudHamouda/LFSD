"""
Intelligence Layer Models — Pipeline Trace Persistence.

Stores complete pipeline execution traces for audit, compliance,
debugging, and the learning loop.

Supplements (does not replace) existing VivLog and AuditLog.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    JSON,
    String,
    Text,
    Index,
)
from sqlalchemy.sql import func

from .database import Base


def _generate_uuid() -> str:
    return str(uuid.uuid4())


class PipelineTraceRecord(Base):
    """
    Complete audit record for a single intelligence pipeline execution.

    Append-only. Never delete rows. Every field is indexed and queryable.
    This is the raw material for the learning loop.
    """

    __tablename__ = "intelligence_traces"

    __table_args__ = (
        Index("idx_trace_user_timestamp", "user_id", "timestamp"),
        Index("idx_trace_tier", "tier"),
        Index("idx_trace_intent", "intent_type"),
        {"extend_existing": True},
    )

    # Identity
    execution_id = Column(String(36), primary_key=True, default=_generate_uuid)
    request_id = Column(String(36), index=True, nullable=True)
    user_id = Column(String, index=True, nullable=False)
    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    # Classification
    tier = Column(Integer, default=0, nullable=False)
    intent_type = Column(String(100), index=True, nullable=True)
    confidence = Column(Float, default=0.0, nullable=False)

    # Stage outputs (JSON snapshots)
    score_deltas_json = Column(JSON, nullable=True)
    action_plan_json = Column(JSON, nullable=True)

    # Response
    response_text = Column(Text, nullable=True)

    # Token accounting
    input_tokens = Column(Integer, default=0, nullable=False)
    output_tokens = Column(Integer, default=0, nullable=False)

    # Performance
    latency_ms = Column(Float, default=0.0, nullable=False)
    stage_timings_json = Column(JSON, nullable=True)

    # Execution result
    execution_success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)

    # Phase 2: Cost tracking
    estimated_cost_usd = Column(Float, default=0.0, nullable=False)
    tradeoff_resolution = Column(
        String(20), nullable=True
    )  # proceed/clarify/escalate/safe_minimal


class DecisionRecord(Base):
    """
    Small, immutable, audit-ready record derived from PipelineTrace.

    Purpose: Fast queryable log of every decision made—without the full
    JSON payloads of PipelineTrace. Think of this as the "receipt".

    Append-only. Never update or delete.
    """

    __tablename__ = "decision_records"

    __table_args__ = (
        Index("idx_decision_user_timestamp", "user_id", "timestamp"),
        Index("idx_decision_tier_intent", "tier", "intent_type"),
        {"extend_existing": True},
    )

    # Identity (FK to intelligence_traces)
    id = Column(String(36), primary_key=True, default=_generate_uuid)
    execution_id = Column(String(36), index=True, nullable=False)
    user_id = Column(String, index=True, nullable=False)
    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # What was decided
    intent_type = Column(String(100), nullable=False)
    tier = Column(Integer, default=0, nullable=False)
    confidence = Column(Float, default=0.0, nullable=False)
    action_type = Column(
        String(50), nullable=True
    )  # respond_only, execute_financial, etc.

    # Tri-dimensional impact (denormalized for fast queries)
    wealth_delta = Column(Float, default=0.0, nullable=False)
    health_delta = Column(Float, default=0.0, nullable=False)
    time_delta = Column(Float, default=0.0, nullable=False)
    net_impact = Column(String(20), nullable=True)  # positive/negative/neutral/mixed

    # Tradeoff resolution
    tradeoff_resolution = Column(String(20), nullable=True)
    has_tradeoff = Column(Boolean, default=False, nullable=False)

    # Cost
    total_tokens = Column(Integer, default=0, nullable=False)
    estimated_cost_usd = Column(Float, default=0.0, nullable=False)

    # Outcome
    execution_success = Column(Boolean, default=True, nullable=False)
