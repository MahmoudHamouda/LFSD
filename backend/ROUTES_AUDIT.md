# Routes Folder - Critical Issues Audit

**Date**: 2026-01-25  
**Severity**: 🚨 **P0 - CRITICAL**  
**Files Reviewed**: 34 route files  
**Issues Found**: 100+

---

## 🔥 Top 5 Catastrophic Issues

### 1. **"default_user" / "pending_user" Data Pollution**
**Impact**: Multiple users writing to the same fake user, causing data collisions

**Locations**:
- `api_routes_indexes.py` - `user_id = "default_user"`
- `api_routes_onboarding.py` - `user_id = "default_user"`
- `api_routes_user.py` - `user_id = "default_user"` in PATCH /me
- `calendar_routes.py` - `user_id = "pending_user"`
- `api_routes_session.py` - Hardcoded dev flags

**Why This Kills You**:
- Test data mixed with real user data
- Analytics are poisoned
- Scoring calculations fail
- Frontend sees garbage data

---

### 2. **Dual/Triple Auth Systems Conflict**
**Impact**: Split identities, duplicate users, broken sessions

**Systems**:
1. **Auth0** (`auth0_routes.py`) - Creates users in /callback
2. **Custom JWT** (`user_routes.py`) - /register, /token
3. **Session-based** (`api_routes_session.py`) - Cookie auth

**Conflicts**:
- Each creates users independently
- Different onboarding logic
- Different JWT claim structures
- No single source of truth

---

### 3. **4 Different Transaction Models**
**Impact**: Financial data split across parallel universes

**Models in Use**:
1. `Transaction` (legacy)
2. `FinancialTransaction` (current)
3. `transactions` table (raw SQL)
4. `transactions_v2` table (migration)

**Routes Using Wrong Models**:
- `api_routes_history.py` - Uses `Transaction` ❌
- `seed_qa_users.py` - Uses `Transaction` ❌
- `api_routes_finance.py` - Uses `FinancialTransaction` ✅
- Raw SQL seeders - Use `transactions_v2` ⚠️

**Result**: Finance dashboards show incomplete data

---

### 4. **GET Endpoints That Mutate State**
**Impact**: Breaks caching, retries, idempotency, infrastructure assumptions

**Culprits**:
| Route | Endpoint | Side Effect |
|-------|----------|-------------|
| `auth0_routes.py` | GET /me | Seeds user data |
| `api_routes_scores.py` | GET /scores/latest | Creates VivIndex |
| `api_routes_user.py` | GET /me | Creates FinancialProfile |
| `history_routes.py` | POST /generate | Writes to disk |

**Why This Is Deadly**:
- Load balancers retry GETs → duplicate data
- CDNs cache → stale mutations
- Monitoring "reads" trigger writes
- Database locks during "read-only" queries

---

### 5. **No Auth on Dangerous Endpoints**
**Impact**: Anyone can delete all data, read other users' PII, impersonate users

**Critical Examples**:
```python
# history_routes.py
@router.delete("/delete_all")  # ❌ NO AUTH
async def delete_all_conversations():
    # Deletes EVERYONE's conversations
    
# api_routes_chat.py  
@router.post("/{session_id}/message")  # ❌ User ID from payload
async def handle_message(data: ChatMessageRequest):
    user_id = data.user_id  # Client controls this!
    
# api_routes_time.py
@router.post("/users/{user_id}/manual")  # ❌ NO user check
async def create_manual_event(user_id: str, ...):
    # Any user can write to any user's calendar
```

---

## 📊 Issue Statistics

### By Category
| Category | Count | Severity |
|----------|-------|----------|
| **No Authentication** | 12 endpoints | 🔴 P0 |
| **User ID from Client** | 8 endpoints | 🔴 P0 |
| **Duplicate Routes** | 15 files | 🟠 P1 |
| **GET Mutates State** | 6 endpoints | 🟠 P1 |
| **Fake/Stub Endpoints** | 9 endpoints | 🟡 P2 |
| **Schema Drift** | 20+ locations | 🟡 P2 |
| **No Pagination** | 14 endpoints | 🟡 P2 |

### By File Severity
| File | Issues | Priority |
|------|--------|----------|
| `history_routes.py` | 11 | 🔴 DELETE |
| `api_routes_history.py` | 8 | 🔴 FIX URGENT |
| `auth0_routes.py` | 7 | 🟠 HARDEN |
| `api_routes_scores.py` | 9 | 🟠 REFACTOR |
| `user_routes.py` | 6 | 🔴 DELETE (duplicate) |
| `financial_routes.py` | 5 | 🔴 DELETE (duplicate) |

---

## 🗑️ Routes to DELETE (Duplicates)

### Complete Duplicates
1. ❌ **`user_routes.py`** - Duplicate of `auth0_routes.py`
   - Both have /register, /token, /me
   - Choose Auth0 as canonical

2. ❌ **`financial_routes.py`** (stub version) - Duplicate of `api_routes_finance.py`
   - Fake pagination
   - Hardcoded data

3. ❌ **`history_routes.py`** - Different from `api_routes_history.py` but BOTH BROKEN
   - No auth on /delete_all
   - Writes to disk
   - Wrong Transaction model

4. ❌ **`test_routes.py`** - Dev only, should not be in prod routes

### Stub/Fake Routes (Mark as TODO or Delete)
5. ❌ **`notification_routes.py`** - Always returns empty
6. ❌ **`partner_routes.py`** - All hardcoded fake data
7. ❌ **`mobility_routes.py`** - No persistence
8. ❌ **`chat_routes.py`** (stub) - No persistence
9. ❌ **`feedback_routes.py`** (stub) - No persistence

---

## 🔧 Critical Fixes Required

### Fix 1: Identity System (Choose One)
**Current State**: 3 auth systems conflict

**Decision Required**:
```
Option A: Auth0 Only
- Keep: auth0_routes.py
- Delete: user_routes.py, api_routes_session.py
- Update: All JWT claims to include user_id, role

Option B: FastAPI Native
- Keep: api_routes_session.py (hardened)
- Delete: auth0_routes.py, user_routes.py
- Add: Proper OAuth if needed

RECOMMENDED: Option A (Auth0)
```

### Fix 2: Transaction Model (Unify)
**Action**:
1. Deprecate `Transaction` model completely
2. Migrate all routes to `FinancialTransaction`
3. Drop `transactions` table, keep only `transactions_v2`
4. Update `api_routes_history.py`:
   ```python
   from models.models import FinancialTransaction  # ✅
   ```

### Fix 3: Remove "default_user" Everywhere
**Files to Fix**:
```python
# api_routes_indexes.py (L10)
- user_id = "default_user"
+ user: User = Depends(get_current_user)
+ user_id = user.id

# api_routes_onboarding.py (L45)
- user_id = "default_user"
+ user_id = current_user.id  # Already has get_current_user

# calendar_routes.py (L28)
- user_id = "pending_user"
+ credentials.user_id = current_user.id
```

### Fix 4: Add Auth to Dangerous Endpoints
```python
# history_routes.py
@router.delete("/delete_all")
+ async def delete_all(current_user: User = Depends(get_current_user)):
-     # Delete all conversations
+     # Delete only current_user's conversations
      db.query(DBConversation).filter(
+         DBConversation.user_id == current_user.id
      ).delete()

# api_routes_time.py
@router.post("/users/{user_id}/manual")
+ async def create_manual_event(
    user_id: str,
+   current_user: User = Depends(get_current_user)
  ):
+   if user_id != current_user.id:
+       raise HTTPException(403, "Cannot modify other users")
```

### Fix 5: Stop Mutating in GET
```python
# auth0_routes.py
@router.get("/me")
async def get_current_user_info(...):
-   seed_user_data(db, user.id, "finance")  # ❌ DELETE THIS
    return {
        "id": user.id,
        ...
    }

# Move seeding to:
# - POST /onboarding/complete
# - Background job after signup
```

---

## 📋 Route Consolidation Plan

### Keep These (Canonical)
```
✅ auth0_routes.py          - Primary auth
✅ api_routes_finance.py    - Finance data
✅ api_routes_health.py     - Health integrations
✅ api_routes_time.py       - Calendar/time (harden auth)
✅ api_routes_goals.py      - Goals (fix schema)
✅ api_routes_chat.py       - Chat (add auth)
✅ api_routes_scores.py     - Scoring (refactor)
✅ growth_routes.py         - Subscriptions
✅ recommendation_routes.py  - Recommendations
✅ admin_routes.py          - Admin panel
✅ api_routes_onboarding.py - Onboarding (fix user_id)
```

### Delete These (Duplicates/Stubs)
```
❌ user_routes.py           - Duplicate auth
❌ financial_routes.py      - Duplicate finance
❌ history_routes.py        - Broken + insecure
❌ test_routes.py           - Dev only
❌ notification_routes.py   - Stub
❌ partner_routes.py        - Fake data
❌ mobility_routes.py       - No persistence
❌ chat_routes.py (stub)    - Duplicate
❌ feedback_routes.py       - Stub
❌ api_routes_session.py    - Conflicting auth
```

### Quarantine for Review
```
⚠️ api_routes_history.py    - Fix Transaction model first
⚠️ calendar_routes.py       - Fix auth + persistence
⚠️ api_routes_indexes.py    - Remove hardcoded user
⚠️ api_routes_user.py       - Conflicts with Auth0
⚠️ whatsapp_routes.py       - Add signature verification
⚠️ bug_routes.py            - Fix user identity
⚠️ audit_routes.py          - Currently stub
⚠️ analytics_routes.py      - Fix JSON parsing
```

---

## 🔒 Security Checklist Per Route

### Required for ALL Routes:
- [ ] Authentication via `Depends(get_current_user)`
- [ ] User ID from auth context (NOT from payload)
- [ ] Input validation with Pydantic models
- [ ] Ownership checks (`resource.user_id == current_user.id`)
- [ ] Rate limiting on heavy endpoints
- [ ] HTTP timeouts on external calls
- [ ] Proper exception handling (no raw `raise e`)

### Forbidden Patterns:
- ❌ `user_id = "default_user"`
- ❌ `user_id = data.user_id` (from payload)
- ❌ `requests.get(url)` (no timeout)
- ❌ `return ORM_object` (serialize first)
- ❌ Mutations in GET endpoints
- ❌ `print()` statements in prod
- ❌ Hardcoded credentials/URLs

---

## 🎯 Recommended Action Plan

### Phase 1: Emergency Fixes (Do Today)
1. **Add auth** to `/delete_all` endpoints
2. **Remove** "default_user" from indexes/onboarding
3. **Block** stub routes from production deployment
4. **Add timeouts** to Auth0 calls

### Phase 2: Consolidation (This Week)
1. **Choose auth system** (Auth0 OR custom)
2. **Delete duplicate** route files
3. **Fix Transaction** model everywhere
4. **Remove GET mutations**

### Phase 3: Architecture (Next Sprint)
1. **Move business logic** to services/
2. **Add proper pagination** everywhere
3. **Implement** background jobs for heavy tasks
4. **Standardize** response schemas

---

## 📈 Impact Metrics (If Fixed)

| Metric | Current | After Cleanup | Improvement |
|--------|---------|---------------|-------------|
| Route Files | 34 | ~18 | -47% |
| Auth Systems | 3 | 1 | -67% |
| Unauthenticated Endpoints | 12 | 0 | -100% |
| Duplicate APIs | 15 | 0 | -100% |
| Fake/Stub Routes | 9 | 0 (marked TODO) | -100% |
| GET Mutations | 6 | 0 | -100% |

---

## 🚨 Most Dangerous Files (Priority Order)

1. **`history_routes.py`** - Delete all without auth
2. **`api_routes_chat.py`** - User impersonation
3. **`api_routes_time.py`** - Write to any user
4. **`user_routes.py`** - Conflicting auth
5. **`api_routes_indexes.py`** - Hardcoded user

---

**Status**: 🚨 CRITICAL - Routes folder needs immediate triage  
**Next Step**: Delete duplicates + add auth guards  
**Estimated Effort**: 2-3 days for critical fixes

---
*Created: 2026-01-25*  
*Files Audited: 34*  
*Critical Issues: 45+*  
*Must-Fix Issues: 18*
