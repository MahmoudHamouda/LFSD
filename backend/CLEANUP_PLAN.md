# Legacy Code Cleanup Recommendations

## Overview
The `backend/` directory contains several legacy folders and services that create technical debt, security risks, and operational complexity.

---

## 🔴 High Priority: Remove or Refactor

### 1. `legacy_v1/` folder
**Status**: Should be archived or deleted

**Issues**:
- Contains old microservice architecture that's been superseded
- Duplicate implementations of auth, config, logging
- Uses outdated patterns (Flask blueprints vs FastAPI routers)
- Security vulnerabilities in `legacy_v1/shared/auth.py` (custom JWT without proper validation)

**Current Dependencies**:
- `services/controllers/feedback_controller.py` imports `legacy_v1.shared.auth.token_required`
- Some chat services reference `legacy_v1/shared/db_connection.py`

**Migration Path**:
1. Move `token_required` decorator to `core/authentication.py` (FastAPI compatible)
2. Update all imports to use centralized modules
3. Archive `legacy_v1/` to a separate repository or delete

---

### 2. `services/audit_log_service/` folder
**Status**: **DEPRECATED** (see `DEPRECATION_AUDIT_LOG_SERVICE.md`)

**Issues**:
- Duplicate of `services/audit_service.py`
- Standalone Flask app creates deployment complexity
- No authentication, allows audit tampering
- Conflicts with `models/logging_models.py::AuditLog`

**Action**: Delete folder after confirming no active callers

---

### 3. `services/chat_service/` folder
**Status**: Partially integrated but inconsistent

**Issues**:
- Separate Flask app (`app.py`) not integrated with main FastAPI app
- Uses different ORM session management than main app
- Database initialization conflicts

**Recommendation**:
- Migrate routes to `routes/api_routes_chat.py` (already exists)
- Use centralized database session from `models/database.py`
- Remove standalone Flask app

---

### 4. `services/controllers/` folder
**Status**: Orphaned controllers

**Issues**:
- Contains `feedback_controller.py` which is a Flask Blueprint
- Main app uses FastAPI routers, not Flask blueprints
- Inconsistent with project architecture

**Action**: 
- Migrate to FastAPI router in `routes/` directory
- Remove `services/controllers/` folder

---

## 🟡 Medium Priority: Consolidate

### 5. Multiple configuration systems
**Current State**:
- `core/config.py` (FastAPI/Pydantic - **USE THIS**)
- `legacy_v1/shared/config.py` (Flask - deprecated)
- `services/chat_service/app.py` tries to load Flask config

**Action**: Standardize on `core/config.py` everywhere

---

### 6. Database connection duplication
**Current State**:
- `models/database.py` - Main app (SQLAlchemy with FastAPI)
- `legacy_v1/shared/db_connection.py` - Legacy Flask
- `services/chat_service/db.py` - Standalone service

**Action**: Use `models/database.py::get_db()` dependency injection pattern

---

## 🟢 Low Priority: Document

### 7. `scripts/` directory
**Status**: Mixed quality

**Recommendation**:
- Audit all scripts for security (API keys, credentials)
- Add README documenting purpose and usage
- Consider moving to a separate `/tools` or `/migrations` directory

---

## Proposed Cleanup Plan

### Phase 1: Immediate (Week 1)
- [ ] Create deprecation notices for `audit_log_service/` and `legacy_v1/`
- [ ] Stop deploying these services to production
- [ ] Document all known imports/dependencies

### Phase 2: Migration (Week 2-3)
- [ ] Move `token_required` to `core/authentication.py`
- [ ] Migrate `feedback_controller` to FastAPI router
- [ ] Consolidate chat service routes
- [ ] Update all imports

### Phase 3: Removal (Week 4)
- [ ] Delete `services/audit_log_service/`
- [ ] Archive `legacy_v1/` to separate repo
- [ ] Remove `services/controllers/`
- [ ] Clean up unused scripts

---

## Benefits of Cleanup

1. **Security**: Remove duplicate, unpatched auth/audit systems
2. **Maintainability**: Single source of truth for each concern
3. **Performance**: Eliminate redundant services and database connections
4. **Onboarding**: Clearer codebase for new developers
5. **Deployment**: Simpler infrastructure (one app, not 3+ microservices)

---

*Created: 2026-01-25*  
*Owner: Engineering Team*
