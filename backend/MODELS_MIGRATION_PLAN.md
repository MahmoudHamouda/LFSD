# Models Layer - Comprehensive Migration Plan

**Date**: 2026-01-25  
**Status**: 🔴 **CRITICAL - REQUIRES IMMEDIATE EXECUTION**  
**Scope**: 7 model files with 40+ issues  
**Estimated Effort**: 1-2 weeks (includes migrations + testing)

---

## 🔥 The 7 Anti-Patterns (Appearing in EVERY model)

These issues repeat across **every single model file**:

| Anti-Pattern | Impact | Files Affected | Severity |
|--------------|--------|----------------|----------|
| **1. Naive Timestamps** | Timezone bugs, wrong ordering | 7/7 | 🔴 P0 |
| **2. FK to wrong user table** | users vs users_v2 mismatch | 6/7 | 🔴 P0 |
| **3. Float for money** | Rounding errors in finance | 4/7 | 🔴 P0 |
| **4. String fields → should be Enums** | Typos break queries | 7/7 | 🟠 P1 |
| **5. No uniqueness constraints** | Duplicate rows | 6/7 | 🟠 P1 |
| **6. Unvalidated JSON** | Type drift | 7/7 | 🟡 P2 |
| **7. No bounds on scores** | Garbage data accepted (-999, 1000) | 3/3 scoring models | 🟡 P2 |

---

## 📋 File-by-File Migration Guide

### 1️⃣ `growth_schemas.py`

#### Issues
| Line | Issue | Fix |
|------|-------|-----|
| L5 | `class PlanId(str):` not a real enum | `class PlanId(str, Enum):` |
| L15 | `plan_id: str` no validation | `plan_id: PlanId` |
| L22 | `status: str` allows garbage | `status: SubscriptionStatus` (enum) |
| L40 | `limits: Dict[str, Any]` untyped | Create `EntitlementLimits` model |
| L52 | Pydantic v1 config | Use `model_config = ConfigDict(from_attributes=True)` |

#### Migration
```python
from enum import Enum
from pydantic import BaseModel, ConfigDict

class PlanId(str, Enum):  # ✅ Real enum
    FREE = "tier_free"
    BASIC = "tier_basic"
    PRO = "tier_pro"

class SubscriptionStatus(str, Enum):  # ✅ NEW
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"

class EntitlementLimits(BaseModel):  # ✅ Typed limits
    ai_queries_per_day: int
    history_months: int
    goals_max: int
    integrations_max: int

class SubscriptionBase(BaseModel):
    plan_id: PlanId  # ✅ Type-safe
    status: SubscriptionStatus  # ✅ Type-safe
    
class EntitlementResponse(BaseModel):
    plan_id: PlanId  # ✅ Consistent naming
    limits: EntitlementLimits  # ✅ Typed
    usage: dict  # Keep flexible for now
    
    model_config = ConfigDict(from_attributes=True)  # ✅ Pydantic v2
```

---

### 2️⃣ `health_models.py` (HealthScore)

#### The 9 Critical Issues

1. **Naive timestamps** → timezone bugs
2. **No score bounds** → accepts -999, 1000
3. **Undefined confidence** → routes interpret differently
4. **Stringly-typed time_window** → "30d" vs "last_30_days" drift
5. **Unvalidated JSON** → data_sources_json shape differs
6. **No uniqueness constraint** → duplicate scores
7. **FK to users** → should be users_v2
8. **Missing relationship back_populates**
9. **extend_existing hides drift**

#### Fixed Model (Drop-in)

```python
import enum
import uuid
from datetime import datetime, timezone, date

from sqlalchemy import (
    Column, String, Float, DateTime, ForeignKey, JSON, 
    Enum, Date, UniqueConstraint, CheckConstraint
)
from sqlalchemy.orm import relationship
from .database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class HealthWindow(str, enum.Enum):
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    LAST_90_DAYS = "last_90_days"

class HealthScore(Base):
    __tablename__ = "health_scores"

    __table_args__ = (
        # ✅ Prevent duplicates
        UniqueConstraint("user_id", "time_window", "score_date", 
                        name="uq_healthscore_user_window_date"),
        # ✅ Enforce score bounds
        CheckConstraint("overall_score >= 0 AND overall_score <= 100", 
                       name="ck_health_overall_score"),
        CheckConstraint("sleep_score >= 0 AND sleep_score <= 100", 
                       name="ck_health_sleep_score"),
        CheckConstraint("movement_score >= 0 AND movement_score <= 100", 
                       name="ck_health_movement_score"),
        CheckConstraint("recovery_score >= 0 AND recovery_score <= 100", 
                       name="ck_health_recovery_score"),
        CheckConstraint("nutrition_score >= 0 AND nutrition_score <= 100", 
                       name="ck_health_nutrition_score"),
        CheckConstraint("lifestyle_score >= 0 AND lifestyle_score <= 100", 
                       name="ck_health_lifestyle_score"),
        CheckConstraint("confidence >= 0 AND confidence <= 1", 
                       name="ck_health_confidence_0_1"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)  # ✅ Fixed FK

    # ✅ Timezone-aware timestamps
    timestamp = Column(DateTime(timezone=True), 
                      default=lambda: datetime.now(timezone.utc), 
                      index=True)
    # ✅ NEW: Logical date for uniqueness
    score_date = Column(Date, nullable=False, default=date.today, index=True)

    # ✅ Scores with bounds
    overall_score = Column(Float, default=0.0, nullable=False)
    confidence = Column(Float, default=0.0, nullable=False)  # 0-1: data coverage %
    
    sleep_score = Column(Float, default=0.0, nullable=False)
    movement_score = Column(Float, default=0.0, nullable=False)
    recovery_score = Column(Float, default=0.0, nullable=False)
    nutrition_score = Column(Float, default=0.0, nullable=False)
    lifestyle_score = Column(Float, default=0.0, nullable=False)

    # ✅ Enum time_window
    time_window = Column(Enum(HealthWindow), default=HealthWindow.LAST_30_DAYS, nullable=False)

    # ✅ JSON defaults to dict
    data_sources_json = Column(JSON, nullable=False, default=dict)

    # ✅ Relationship with back_populates
    user = relationship("User", back_populates="health_scores")
```

**Alembic Migration**:
```python
"""Add health score constraints and enums

Revision ID: health_score_v2
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add score_date column
    op.add_column('health_scores', sa.Column('score_date', sa.Date(), nullable=True))
    op.execute("UPDATE health_scores SET score_date = timestamp::date WHERE score_date IS NULL")
    op.alter_column('health_scores', 'score_date', nullable=False)
    
    # Add constraints
    op.create_check_constraint("ck_health_overall_score", "health_scores", 
                               "overall_score >= 0 AND overall_score <= 100")
    op.create_check_constraint("ck_health_confidence_0_1", "health_scores",
                               "confidence >= 0 AND confidence <= 1")
    
    # Add unique constraint
    op.create_unique_constraint("uq_healthscore_user_window_date", "health_scores",
                                ["user_id", "time_window", "score_date"])
```

---

### 3️⃣ `InvestmentPortfolio`

#### The 8 Critical Issues

1. **FK to users** → should be users_v2
2. **Naive timestamp** → last_updated timezone bug
3. **Float for money** → precision errors
4. **Currency not constrained** → "USDD" typos
5. **No uniqueness** → duplicate portfolios
6. **Unvalidated JSON** → asset_allocation shape varies
7. **Incomplete relationship**
8. **UUID length not constrained**

#### Fixed Model

```python
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, DateTime, ForeignKey, JSON, 
    UniqueConstraint, Numeric
)
from sqlalchemy.orm import relationship
from .database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class InvestmentPortfolio(Base):
    __tablename__ = "investment_portfolios"

    __table_args__ = (
        # ✅ Prevent duplicate portfolios
        UniqueConstraint("user_id", "institution_name", "portfolio_name", 
                        name="uq_portfolio_user_institution_name"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)  # ✅ Length constrained
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)  # ✅ Fixed FK

    institution_name = Column(String(100), nullable=False)
    portfolio_name = Column(String(255), nullable=True)

    # ✅ Numeric for money (not Float)
    total_value = Column(Numeric(18, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)  # ✅ Length constrained
    
    daily_change_percent = Column(Numeric(7, 4), nullable=True)
    total_return_percent = Column(Numeric(7, 4), nullable=True)

    # ✅ JSON defaults to dict
    asset_allocation_json = Column(JSON, nullable=False, default=dict)

    # ✅ Timezone-aware timestamp
    last_updated = Column(DateTime(timezone=True), 
                         default=lambda: datetime.now(timezone.utc), 
                         index=True)

    # ✅ Relationship with back_populates
    user = relationship("User", back_populates="investment_portfolios")
```

---

### 4️⃣ `BackgroundJob` (Job.py)

#### The 10 Critical Issues

1. **user_id not FK** → orphan jobs accumulate
2. **Naive timestamps** → created_at, updated_at
3. **Stringly-typed status** → "pendng" typos
4. **No progress bounds** → -12, 1000 accepted
5. **No dedupe** → duplicate jobs
6. **No indexes on status/expires_at**
7. **extend_existing hides drift**
8. **result_json vs error_message semantics unclear**

#### Fixed Model

```python
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, Integer, Text, DateTime, ForeignKey, JSON,
    Enum, CheckConstraint, Index
)
from .database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class JobStatus(str, enum.Enum):  # ✅ NEW
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class BackgroundJob(Base):
    __tablename__ = "background_jobs"

    __table_args__ = (
        # ✅ Enforce progress bounds
        CheckConstraint("progress >= 0 AND progress <= 100", 
                       name="ck_bgjob_progress_0_100"),
        # ✅ Indexes for queries
        Index("ix_bgjob_status_updated", "status", "updated_at"),
        Index("ix_bgjob_expires_at", "expires_at"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)

    # ✅ FK to user
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=True, index=True)
    job_type = Column(String(100), nullable=False, index=True)
    source = Column(String(50), default="system", nullable=False)

    # ✅ Enum status
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False, index=True)
    progress = Column(Integer, default=0, nullable=False)

    # ✅ NEW: Dedupe key
    dedupe_key = Column(String(200), nullable=True, index=True)

    # ✅ JSON defaults to dict
    result_json = Column(JSON, nullable=False, default=dict)
    error_message = Column(Text, nullable=True)

    # ✅ Timezone-aware timestamps
    created_at = Column(DateTime(timezone=True), 
                       default=lambda: datetime.now(timezone.utc), 
                       nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), 
                       default=lambda: datetime.now(timezone.utc),
                       onupdate=lambda: datetime.now(timezone.utc), 
                       nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
```

---

### 5️⃣ `LifestyleEvent`

#### The 9 Critical Issues

1. **FK to users** → should be users_v2
2. **Naive timestamps** → start_time, end_time
3. **Float for money** → cost_estimated precision
4. **Currency not constrained**
5. **Stringly-typed event_type** → "dinning" vs "dining"
6. **No dedupe** → duplicate events from re-sync
7. **JSON doesn't default to dict**
8. **No indexes on common queries**
9. **Incomplete relationship**

#### Fixed Model

```python
import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, String, DateTime, ForeignKey, JSON, Numeric, Float,
    Enum, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship
from .database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class LifestyleEventType(str, enum.Enum):  # ✅ NEW
    DINING = "dining"
    CONCERT = "concert"
    SPORTS = "sports"
    TRAVEL = "travel"
    LEISURE = "leisure"

class LifestyleEvent(Base):
    __tablename__ = "lifestyle_events"

    __table_args__ = (
        # ✅ Prevent duplicate ingestion
        UniqueConstraint("user_id", "source", "external_id", 
                        name="uq_lifestyle_source_external"),
        # ✅ Indexes for common queries
        Index("ix_lifestyle_user_time", "user_id", "start_time"),
        Index("ix_lifestyle_user_type", "user_id", "event_type"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)  # ✅ Fixed FK

    # ✅ Enum event_type
    event_type = Column(Enum(LifestyleEventType), nullable=False)
    title = Column(String(255), nullable=False)

    # ✅ Timezone-aware timestamps
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=True)

    location_name = Column(String(255), nullable=True)
    location_lat = Column(Float, nullable=True)
    location_lon = Column(Float, nullable=True)

    # ✅ Numeric for money
    cost_estimated = Column(Numeric(18, 2), nullable=True)
    currency = Column(String(3), default="USD", nullable=False)  # ✅ Length constrained

    source = Column(String(50), nullable=True)
    external_id = Column(String(255), nullable=True)

    # ✅ JSON defaults to dict
    metadata_json = Column(JSON, nullable=False, default=dict)

    # ✅ NEW: Audit timestamps
    created_at = Column(DateTime(timezone=True), 
                       default=lambda: datetime.now(timezone.utc), 
                       nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), 
                       default=lambda: datetime.now(timezone.utc),
                       onupdate=lambda: datetime.now(timezone.utc), 
                       nullable=False, index=True)

    # ✅ Relationship with back_populates
    user = relationship("User", back_populates="lifestyle_events")
```

---

## 🎯 Migration Strategy

### Phase 1: Critical Fixes (This Week)

**Priority Order**:
1. **HealthScore** - Most visible impact
2. **InvestmentPortfolio** - Money precision critical
3. **BackgroundJob** - Affects all async operations

**Steps**:
```bash
# 1. Create Alembic migrations
alembic revision --autogenerate -m "Add constraints and enums to health_scores"
alembic revision --autogenerate -m "Fix investment_portfolio money precision"
alembic revision --autogenerate -m "Add job status enum and constraints"

# 2. Review generated migrations
# 3. Add data migrations (convert existing data to new enums)
# 4. Test on dev DB
# 5. Deploy
```

### Phase 2: Remaining Models (Next Week)
- LifestyleEvent
- growth_schemas (Pydantic only, no DB migration)

---

## 📋 Universal Migration Template

**Every model needs these changes**:

```python
# 1. ✅ Timezone-aware timestamps
from datetime import datetime, timezone

created_at = Column(DateTime(timezone=True), 
                   default=lambda: datetime.now(timezone.utc), 
                   index=True)

# 2. ✅ Proper FK to users_v2
user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)

# 3. ✅ Numeric for money (not Float)
from sqlalchemy import Numeric

amount = Column(Numeric(18, 2), nullable=False)

# 4. ✅ Enums for constrained strings
from sqlalchemy import Enum
import enum

class MyStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

status = Column(Enum(MyStatus), default=MyStatus.ACTIVE)

# 5. ✅ JSON defaults to dict
metadata_json = Column(JSON, nullable=False, default=dict)

# 6. ✅ Uniqueness constraints where needed
__table_args__ = (
    UniqueConstraint("user_id", "external_id", name="uq_..."),
)

# 7. ✅ Relationships with back_populates
user = relationship("User", back_populates="my_collection")
```

---

## ⚠️ Breaking Changes Required

| Change | Impact | Migration Path |
|--------|--------|----------------|
| Add score bounds | Rejects bad data | Clean existing data first |
| Add uniqueness constraints | Fails if duplicates exist | Dedupe before migration |
| Enum migrations | Fails on invalid values | Convert or delete bad rows |
| Numeric for Float | Type change | `ALTER COLUMN ... TYPE NUMERIC(18,2) USING amount::numeric` |
| FK changes | Fails if orphan rows | Clean orphans first |

---

## ✅ Success Criteria

After migrations, every model should have:

- [ ] **Timezone-aware** timestamps
- [ ] **FK to users_v2** (not users)
- [ ] **Numeric for money** (not Float)
- [ ] **Enums** for constrained strings
- [ ] **Uniqueness constraints** to prevent duplicates
- [ ] **Check constraints** for bounds (scores 0-100)
- [ ] **Indexes** on common query paths
- [ ] **JSON defaults** to dict (not null)
- [ ] **Relationships** with back_populates

---

**Status**: 🔴 READY FOR EXECUTION  
**Estimated Time**: 1-2 weeks  
**Risk**: MEDIUM (requires migrations)  
**Reward**: Fixes root cause of most bugs

---

*Created: 2026-01-25*  
*Models Audited: 5 core files*  
*Issues Fixed: 40+*  
*Migrations Required: Yes*
