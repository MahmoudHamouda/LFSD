"""
Outcome Models — "What Happened After We Decided"

The other half of the audit trail. DecisionRecord captures "what we decided."
OutcomeRecord captures "what happened after we decided."

Together they form the reinforcement signal for the learning loop.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from db.base import Base


class OutcomeRecord(Base):
    """
    Immutable outcome record for a pipeline decision.

    Created after execution completes (or is skipped/cancelled).
    Links back to DecisionRecord via execution_id.

    This is the reinforcement signal — did the decision lead to a good outcome?
    """

    __tablename__ = "intelligence_outcomes"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Link to DecisionRecord
    execution_id = Column(
        String(64),
        nullable=False,
        index=True,
    )

    user_id = Column(String(64), nullable=False, index=True)
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Execution outcome
    executed = Column(Boolean, default=False, nullable=False)
    execution_gate = Column(String(32), default="allow")  # allow/confirm/deny
    partner_call_status = Column(
        String(32), default="skipped"
    )  # success/failure/timeout/skipped

    # User interaction
    user_confirmed = Column(Boolean, default=False)
    user_rejected = Column(Boolean, default=False)
    confirmation_latency_ms = Column(Integer, default=0)

    # Completion
    completed = Column(Boolean, default=False)
    cancelled = Column(Boolean, default=False)
    time_to_complete_ms = Column(Integer, default=0)

    # User satisfaction
    user_satisfaction = Column(
        Integer, default=0
    )  # -1 (thumbs down), 0 (no signal), +1 (thumbs up)
    satisfaction_comment = Column(Text, nullable=True)

    # Error tracking
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    # Context for learning
    intent_type = Column(String(64), nullable=False, default="unknown")
    tier = Column(Integer, default=0)
    tradeoff_resolution = Column(String(32), nullable=True)

    __table_args__ = (
        Index("ix_outcomes_user_time", "user_id", "timestamp"),
        Index("ix_outcomes_intent", "intent_type"),
        Index("ix_outcomes_satisfaction", "user_satisfaction"),
    )

    def __repr__(self):
        return (
            f"<OutcomeRecord execution_id={self.execution_id} "
            f"executed={self.executed} completed={self.completed} "
            f"satisfaction={self.user_satisfaction}>"
        )
