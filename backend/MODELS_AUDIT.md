# Models Layer - Critical Audit & Refactoring Plan

**Date**: 2026-01-25  
**Severity**: 🚨 **P0 - ARCHITECTURAL**  
**Scope**: Foundation layer that all routes/services depend on  
**Status**: 🔴 **REQUIRES IMMEDIATE REFACTORING**

---

## 🔥 Root Cause Analysis

Your models layer has **4 fundamental flaws** that cascade into every other part of the system:

### 1. **Schema Sprawl Without Ownership**
The same concept is defined in 3-4 different places with no single source of truth.

**Example - Feedback**:
- `models/chat_models.py::Feedback`
- `services/chat_service/schemas/feedback.py` (deleted)
- `services/chat_service/schemas/feedback_schema.py` (deleted)
- `api_models.py::FeedbackCreate`

**Example - Goals**:
- `models/models.py::LifeGoal`
- `api_models.py::Goal`
- `api_models.py::GoalCreate`
- Multiple route-specific variations

### 2. **Financial Bias Contaminating All Pillars**
Models designed for finance are forced onto health/time/productivity.

**Evidence**:
```python
# LifeGoal model (in models.py)
target_amount = Column(Float)        # ❌ Money-biased name
saved_amount = Column(Float)         # ❌ Money-biased name  
monthly_contribution_target = Column(Float)  # ❌ Finance-only

# But used for:
- Health goals (run 100km)
- Time goals (limit meetings to 10h/week)
- Productivity goals (read 12 books)
```

**Result**: Health score = `saved_amount: 21.0` (km run as dollars)

### 3. **Identity is Optional When It Must Be Absolute**
User ID can be null, missing, or client-supplied.

**Evidence**:
```python
# api_models.py
user_id: Optional[str] = None  # ❌ Allows impersonation

# Routes use:
user_id = "default_user"       # ❌ Hardcoded
user_id = data.user_id         # ❌ From client payload

# Should be:
user_id: str = current_user.id  # ✅ From auth context
```

### 4. **JSON Everywhere, Schema Nowhere**
Unvalidated JSON fields store critical data with no type safety.

**Evidence**:
```python
# Unvalidated JSON columns:
profile_json = Column(JSON)           # No schema
viv_preferences = Column(JSON)        # No schema
config_json = Column(JSON)            # No schema
data_sources_json = Column(JSON)      # No schema
overrides_json = Column(JSON)         # No schema
impact_vector_json = Column(JSON)     # No schema

# Routes assume keys exist:
profile_json["google_creds"]          # ❌ May not exist
config_json["ai_queries_per_day"]     # ❌ May not exist
```

---

## 📊 File-by-File Critical Issues

### 1️⃣ `growth_schemas.py`

| Issue | Severity | Impact |
|-------|----------|--------|
| `PlanId` is not an Enum | 🔴 P0 | Any string accepted as plan_id |
| `plan_id: str` everywhere | 🔴 P0 | No validation |
| Untyped `limits` and `usage` dicts | 🟠 P1 | Frontend cannot rely on shape |
| Missing subscription lifecycle fields | 🟡 P2 | Routes assume behavior not in schema |

**Fix**:
```python
from enum import Enum

class PlanId(str, Enum):  # ✅ Real enum
    FREE = "tier_free"
    BASIC = "tier_basic"
    PRO = "tier_pro"

class Subscription(BaseModel):
    plan_id: PlanId  # ✅ Type-safe
    limits: Dict[str, int]  # ✅ Specific type
```

---

### 2️⃣ `health_models.py`

| Issue | Severity | Impact |
|-------|----------|--------|
| `confidence` semantics undefined | 🟠 P1 | Routes interpret differently |
| No score bounds (0-100?) | 🟠 P1 | Garbage data accepted |
| `data_sources_json` unvalidated | 🟠 P1 | Type mismatches |
| No uniqueness constraint | 🟡 P2 | Multiple scores per user/window |

**Fix**:
```python
class DBHealthScore(Base):
    score = Column(Float, CheckConstraint('score >= 0 AND score <= 100'))
    confidence = Column(Float, CheckConstraint('confidence >= 0 AND confidence <= 1'))
    # Add unique constraint
    __table_args__ = (
        UniqueConstraint('user_id', 'time_window', 'created_at', name='uix_user_score'),
    )
```

---

### 3️⃣ `api_models.py` - **THE DUMPING GROUND**

**This file is a disaster** - it mixes:
- Chat models
- Feedback
- History  
- Onboarding
- Goals
- Coverage
- UI config
- Auth info

| Issue | Severity | Impact |
|-------|----------|--------|
| Mixed responsibilities (8+ domains) | 🔴 P0 | Accidental coupling everywhere |
| `ChatMessage.date` is string | 🔴 P0 | Sorting breaks, timezone bugs |
| Mutable default lists (`session_ids: List = []`) | 🔴 P0 | Classic Python bug |
| `user_id` in payloads | 🔴 P0 | Enables impersonation |
| Goal model financially biased | 🔴 P0 | Root cause of goal corruption |
| `GoalType` defined but unused | 🟠 P1 | False sense of safety |
| `monthly_income: float = 0` | 🟠 P1 | Cannot distinguish unknown from zero |

**Fix**: DELETE this file and split into domain-specific schemas.

---

### 4️⃣ `auth_schemas.py`

| Issue | Severity | Impact |
|-------|----------|--------|
| Email-only identity | 🟠 P1 | Missing name, phone, role |
| No password constraints | 🟠 P1 | Security policy undefined |

---

### 5️⃣ `chat_models.py`

| Issue | Severity | Impact |
|-------|----------|--------|
| Integer PKs (`session_id`) | 🟠 P1 | Frontend expects UUIDs |
| `content = String(1000)` too small | 🔴 P0 | LLM responses truncated |
| No cascade deletes | 🟠 P1 | Orphaned data |
| Duplicate Feedback model | 🟡 P2 | Two feedback systems |

**Fix**:
```python
# Increase content size for LLM responses
content = Column(Text)  # ✅ No length limit

# Add cascade
session_id = Column(Integer, ForeignKey("chat_sessions.session_id", ondelete="CASCADE"))
```

---

### 6️⃣ `database.py`

| Issue | Severity | Impact |
|-------|----------|--------|
| Cloud SQL connector never closed | 🔴 P0 | Resource leak under load |
| `getconn()` can return None | 🔴 P0 | Unpredictable failures |
| SQLite fallback path is relative | 🟠 P1 | Breaks in Docker/tests |
| Imports non-existent modules | 🟠 P1 | Deployment failures |
| Mixed prod/dev semantics | 🟡 P2 | Easy to corrupt prod |

**Fix**:
```python
# Proper connector lifecycle
connector = Connector()

def cleanup_connector():
    connector.close()

# Register cleanup
atexit.register(cleanup_connector)

# SQLite absolute path
DATABASE_URL = f"sqlite:///{os.path.abspath('lfsd.db')}"
```

---

### 7️⃣ `growth_models.py`

| Issue | Severity | Impact |
|-------|----------|--------|
| Business logic in defaults | 🟠 P1 | DB decides product behavior |
| No uniqueness constraints | 🔴 P0 | Multiple subscriptions per user |
| Unvalidated `config_json` | 🔴 P0 | Routes assume specific keys |
| Overrides have no expiry/scope | 🟡 P2 | Conflict resolution undefined |

**Fix**:
```python
class Subscription(Base):
    # Enforce one active subscription per user
    __table_args__ = (
        UniqueConstraint('user_id', 'status', 
                        name='uix_user_active_subscription',
                        postgresql_where=Column('status') == 'active'),
    )
```

---

## 🎯 **NON-NEGOTIABLE FIX: Goals Model**

This is the **single most important fix** in the entire codebase.

### Current (Broken):
```python
class LifeGoal(Base):
    target_amount = Column(Float)  # ❌ Money-biased
    saved_amount = Column(Float)   # ❌ Money-biased
    monthly_contribution_target = Column(Float)  # ❌ Finance-only
    pillar = Column(String(50))  # ❌ Not validated
```

### Fixed (Universal):
```python
from enum import Enum

class GoalPillar(str, Enum):
    FINANCE = "finance"
    HEALTH = "health"
    TIME = "time"
    PRODUCTIVITY = "productivity"

class GoalUnit(str, Enum):
    USD = "usd"
    HOURS = "hours"
    KILOMETERS = "km"
    STEPS = "steps"
    DAYS = "days"
    BOOKS = "books"
    PERCENTAGE = "percentage"

class LifeGoal(Base):
    __tablename__ = "life_goals"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)
    
    # Universal fields (not money-biased)
    pillar = Column(Enum(GoalPillar), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Generic progress tracking
    target_value = Column(Float, nullable=False)
    current_value = Column(Float, default=0.0)
    unit = Column(Enum(GoalUnit), nullable=False)
    
    # Metadata
    priority = Column(String(20))  # high, medium, low
    deadline = Column(Date, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
    
    # Remove entirely:
    # - target_amount ❌
    # - saved_amount ❌
    # - monthly_contribution_target ❌
```

**Migration Required**:
```sql
-- Alembic migration to convert existing goals
-- Map saved_amount → current_value
-- Map target_amount → target_value
-- Infer unit from pillar
```

---

## 📋 Refactoring Action Plan

### Phase 1: Critical Fixes (This Week)

#### A. Delete `api_models.py` Dumping Ground
**Action**:
```bash
# Split into domain-specific schemas
schemas/
├── auth.py          # Auth, User, Token
├── finance.py       # Accounts, Transactions
├── health.py        # Daily summaries, workouts
├── time.py          # Calendar events
├── goals.py         # Goals (new universal model)
├── chat.py          # Chat sessions, messages
└── growth.py        # Subscriptions, entitlements
```

#### B. Fix Goals Model (Non-Negotiable)
1. Create new `life_goals_v2` table with universal fields
2. Migrate existing data with unit inference
3. Update all routes to use new model
4. Drop old table after validation

#### C. Enforce User Identity
**Remove from ALL schemas**:
```python
user_id: Optional[str] = None  # ❌ DELETE

# Replace with route-level enforcement:
@router.post("/resource")
async def create_resource(
    data: ResourceCreate,  # ✅ No user_id field
    current_user: User = Depends(get_current_user)
):
    resource = Resource(
        user_id=current_user.id,  # ✅ From auth context
        **data.dict()
    )
```

#### D. Validate JSON Columns
Create Pydantic models for all JSON fields:

```python
class ProfileData(BaseModel):
    name: str
    google_creds: Optional[dict] = None
    preferences: dict = {}

class VivPreferences(BaseModel):
    risk_tolerance: str = "medium"
    # ... other fields

# In model:
profile_json = Column(JSON)  # Still store as JSON

# But validate on read/write:
profile = ProfileData(**user.profile_json)
```

---

### Phase 2: Architectural Cleanup (Next Sprint)

1. **Add DB constraints**:
   - Unique indexes where expected
   - Check constraints for score bounds
   - Foreign key cascades

2. **Fix Cloud SQL connector**:
   - Proper lifecycle management
   - Connection pooling
   - Health checks

3. **Consolidate score models**:
   - One canonical Score model per pillar
   - Consistent `confidence` semantics
   - Proper time windowing

4. **Split User models**:
   - `User` (identity only)
   - `UserProfile` (preferences)
   - `UserSubscription` (growth)

---

## 🚨 Breaking Changes Required

These changes **WILL** break existing code, but are **necessary**:

| Change | Impact | Migration Path |
|--------|--------|----------------|
| Delete `api_models.py` | All imports break | Update to domain schemas |
| Rename goal fields | Goal routes break | Update column names |
| Remove `user_id` from payloads | Auth changes needed | Use `Depends(get_current_user)` |
| Validate JSON schemas | May expose bad data | Clean data first |
| Add uniqueness constraints | Duplicate subs fail | Dedupe before migration |

---

## 📊 Impact if NOT Fixed

| Issue | Current State | If Not Fixed |
|-------|---------------|--------------|
| Goal corruption | Health goals store $$ | Analytics permanently broken |
| Schema sprawl | 3-4 definitions per concept | Impossible to maintain |
| Optional user_id | "default_user" everywhere | Security nightmare continues |
| Unvalidated JSON | Silent failures | Database fills with garbage |

---

## ✅ Success Criteria

After refactoring, you should have:

- [ ] **ONE** canonical model per business concept
- [ ] **ZERO** money-biased fields in universal models
- [ ] **ZERO** optional user IDs in payloads
- [ ] **ALL** JSON fields validated with Pydantic
- [ ] **CLEAR** schema ownership (no dumping grounds)
- [ ] **PROPER** DB constraints (unique, check, cascade)

---

## 🎯 Recommended Execution Order

1. **Today**: Create domain-specific schemas, delete `api_models.py`
2. **Tomorrow**: Fix Goals model (migration + tests)
3. **Day 3**: Remove all `user_id` from request payloads
4. **Week 2**: Add JSON validation
5. **Week 3**: Add DB constraints + fix Cloud SQL connector

---

**Status**: 🚨 CRITICAL - Foundation layer needs immediate refactoring  
**Estimated Effort**: 1-2 weeks for complete fix  
**Risk**: HIGH (breaking changes) but **NECESSARY**  
**Reward**: Fixes root cause of 90% of current bugs

---

*Created: 2026-01-25*  
*Files Audited: 7 core model files*  
*Critical Issues: 30+*  
*Architectural Flaws: 4 fundamental*  
*Breaking Changes Required: Yes*
