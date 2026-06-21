"""
Background Jobs - Async task tracking.

Tracks long-running backend processes like bank sync, data processing, etc.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    JSON,
    Enum,
    CheckConstraint,
    Index,
)
from sqlalchemy.sql import func
from .database import Base


def generate_uuid() -> str:
    """Generate UUID string for primary keys."""
    return str(uuid.uuid4())


class JobStatus(str, enum.Enum):
    """Lifecycle states for background jobs."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class BackgroundJob(Base):
    """
    Async job tracker.

    Used to poll status of long-running tasks.
    """

    __tablename__ = "background_jobs"

    __table_args__ = (
        # Enforce progress bounds
        CheckConstraint(
            "progress >= 0 AND progress <= 100", name="ck_bgjob_progress_0_100"
        ),
        # Indexes for queries
        Index("ix_bgjob_status_updated", "status", "updated_at"),
        Index("ix_bgjob_expires_at", "expires_at"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)

    # ✅ FK to users_v2 (nullable as system jobs might exist)
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=True, index=True)

    job_type = Column(String(100), nullable=False, index=True)
    source = Column(String(50), default="system", nullable=False)

    # ✅ Enum status
    status = Column(
        Enum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True
    )
    progress = Column(Integer, default=0, nullable=False)

    # Idempotency / dedupe key
    dedupe_key = Column(String(200), nullable=True, index=True)

    # Output data
    result_json = Column(JSON, nullable=False, default=dict)
    error_message = Column(Text, nullable=True)

    # ✅ Timezone-aware timestamps
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
    expires_at = Column(DateTime(timezone=True), nullable=True)
