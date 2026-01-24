# Scripts Cleanup & Migration Plan

**Priority**: 🔴 CRITICAL SECURITY RISK  
**Scope**: 34 scripts with hardcoded credentials, inconsistent DB connections, and unsafe patterns

---

## 🔴 Immediate Action Required (Security)

### Critical Security Issues (Delete or Fix Today)

| Script | Issue | Action |
|--------|-------|--------|
| `recreate_time_scores_table.py` | **L10**: Hardcoded DB password + public IP | ❌ DELETE |
| `reset_test_passwords.py` | **L9**: Hardcoded DB password + IP | ❌ DELETE |
| `calc_scores.py` | **L9**: Hardcoded Cloud Run URL | 🔧 FIX or DELETE |
| `check_profile_json.py` | **L14**: Hardcoded DB password | ❌ DELETE |
| `clear_productivity.py` | **L14**: Hardcoded DB password | ❌ DELETE |
| `create_time_scores_table.py` | **L12**: Hardcoded DB password | ❌ DELETE |
| `inspect_user.py` | **L20**: Prints password hashes | 🔧 SANITIZE |
| `authentication.py` | **L24**: Placeholder OAuth URL | ❌ MOVE to routes/ |
| `user_routes.py` | **L10**: Hardcoded SECRET_KEY | ❌ MOVE to routes/ |

**Why Delete**: These scripts hardcode production credentials that are **committed to git**. Even if you rotate credentials, the old ones are in git history forever.

---

## 📊 Database Inconsistency Analysis

### Multiple Database Targets Found

| Script | Database | Issue |
|--------|----------|-------|
| `clear_recommendation_data.py` | SQLite (`lfsd_v2.db`) | ❌ Wrong DB |
| `reset_and_seed_users.py` | Postgres (via SessionLocal) | ✅ Correct |
| `list_all_users.py` | Postgres (via models) | ✅ Correct |
| `recreate_time_scores_table.py` | Postgres (hardcoded URL) | ⚠️ Unsafe |
| 10+ others | Hardcoded Postgres URLs | ⚠️ Credentials leak |

**Problem**: Scripts point to **different databases**. `clear_recommendation_data.py` uses SQLite while the app uses Postgres.

---

## 🗂️ Script Classification

### Category 1: Database Admin (Should be Alembic migrations)
- ❌ `recreate_time_scores_table.py` - DELETE (use Alembic)
- ❌ `create_time_scores_table.py` - DELETE (use Alembic)
- 🔧 `reset_and_seed_users.py` - KEEP but refactor (useful for dev)

### Category 2: Data Inspection (Should be Django/Flask CLI commands)
- 🔧 `list_all_users.py` - Migrate to CLI command
- 🔧 `inspect_user.py` - Migrate to CLI command
- ❌ `check_profile_json.py` - DELETE (API endpoint better)

### Category 3: Data Manipulation (Developer Tools)
- ❌ `clear_productivity.py` - DELETE (use SQL or admin UI)
- ❌ `clear_recommendation_data.py` - DELETE (wrong DB anyway)
- ❌ `reset_test_passwords.py` - DELETE (use seed script)

### Category 4: API Wrappers (Redundant)
- ❌ `calc_scores.py` - DELETE (just call the API directly or use curl)

### Category 5: Routes (Should be moved to routes/ folder)
- ❌ `audit_routes.py` - Already have routes/
- ❌ `feedback_routes.py` - Already consolidated
- ❌ `chat_routes.py` - Already have api_routes_chat.py
- ❌ `recommendation_routes.py` - Already have routes/
- ❌ `partner_routes.py` - Already have routes/
- ❌ `user_routes.py` - Already have routes/
- ❌ `financial_routes.py` - Already have routes/
- ❌ `notification_routes.py` - Already have routes/
- ❌ `activity_feed_routes.py` - Already have routes/

### Category 6: Middleware (Should be in core/)
- ❌ `rate_limiting.py` - Already have core/rate_limiting.py
- ❌ `authentication.py` - Already have core/authentication.py

### Category 7: Config (Should be in core/)
- ❌ `config.py` - Already have core/config.py

### Category 8: Docker (Should be in root or .docker/)
- 🔧 `docker-compose.yml` - Move to root, fix paths
- 🔧 `Dockerfile.*` - Move to .docker/ or root

---

## ✅ Recommended Actions

### Phase 1: Security Remediation (TODAY)

```powershell
# Delete scripts with hardcoded credentials
Remove-Item scripts/recreate_time_scores_table.py
Remove-Item scripts/reset_test_passwords.py
Remove-Item scripts/check_profile_json.py
Remove-Item scripts/clear_productivity.py
Remove-Item scripts/create_time_scores_table.py
Remove-Item scripts/calc_scores.py  # Cloud Run URL hardcoded

# Delete duplicate routes (already in routes/ folder)
Remove-Item scripts/audit_routes.py
Remove-Item scripts/feedback_routes.py
Remove-Item scripts/chat_routes.py
Remove-Item scripts/recommendation_routes.py
Remove-Item scripts/partner_routes.py
Remove-Item scripts/user_routes.py
Remove-Item scripts/financial_routes.py
Remove-Item scripts/notification_routes.py
Remove-Item scripts/activity_feed_routes.py

# Delete duplicate middleware/config
Remove-Item scripts/rate_limiting.py
Remove-Item scripts/authentication.py
Remove-Item scripts/config.py

# Delete wrong-database scripts
Remove-Item scripts/clear_recommendation_data.py  # Uses SQLite
```

### Phase 2: Refactor Useful Scripts (WEEK 1)

**Keep and Harden**:
1. `reset_and_seed_users.py` → Refactor to:
   - Use environment variables for DB
   - Add `--env` flag (dev/staging/prod)
   - Block production unless `--force-production` flag
   - Split into separate files:
     - `migrations/` (Alembic)
     - `scripts/seed_dev_users.py` (safe)
     - `scripts/wipe_dev_db.py` (gated)

2. `list_all_users.py` → Convert to CLI command:
   ```python
   # scripts/cli/list_users.py
   @click.command()
   @click.option('--limit', default=50)
   def list_users(limit):
       """List users from database"""
       # Use get_settings() for DB connection
       # Add pagination
   ```

3. `inspect_user.py` → Convert to CLI command:
   ```python
   # scripts/cli/inspect_user.py
   @click.command()
   @click.argument('email')
   @click.option('--show-hash/--no-show-hash', default=False)
   def inspect_user(email, show_hash):
       """Inspect user details"""
       # Sanitize output, hide password hash by default
   ```

### Phase 3: Docker Cleanup (WEEK 2)

Move Docker files to proper locations:
```
backend/
├── Dockerfile              ← Main app Dockerfile
├── docker-compose.yml      ← Move from scripts/
└── .dockerignore           ← Add this
```

---

## 🔒 Security Best Practices for Scripts

### ✅ DO:
- Read credentials from environment variables
- Use `core/config.py::get_settings()` for DB connection
- Add `--environment` flag (dev/staging/prod)
- Gate destructive operations with confirmations
- Log all script executions to audit log
- Use CLI frameworks (Click, Typer)

### ❌ DON'T:
- Hardcode database URLs
- Hardcode API endpoints
- Use `sys.path` hacks
- Mix schema creation with data seeding
- Print sensitive data (passwords, tokens)
- Use `DROP TABLE CASCADE` without guards

---

## 📋 Migration Checklist

- [ ] Delete 20+ scripts with hardcoded credentials
- [ ] Convert 3 useful scripts to CLI commands
- [ ] Move Docker files to root
- [ ] Create `scripts/cli/` for Click-based commands
- [ ] Add `scripts/README.md` explaining what remains
- [ ] Update `.gitignore` to prevent adding more unsafe scripts
- [ ] Audit git history for leaked credentials → rotate if found

---

## 🎯 Final State

```
backend/
├── scripts/
│   ├── README.md                    ← Usage guide
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── list_users.py           ← Click command
│   │   ├── inspect_user.py         ← Click command
│   │   └── seed_dev_users.py       ← Safe dev seeding
│   └── utils/                       ← Helper functions only
├── Dockerfile
├── docker-compose.yml
└── migrations/                      ← Alembic (schema only)
```

**Scripts count**: 34 → 5 (85% reduction)

---

## ⚠️ Git History Concern

**CRITICAL**: If the hardcoded credentials in these scripts are **real production credentials**, they are now in your git history forever (even after deletion).

**Action Required**:
1. Rotate all database passwords immediately
2. Rotate all API keys (OpenAI, Cloud Run, etc.)
3. Use `git filter-repo` if needed to rewrite history (coordinate with team)
4. Add pre-commit hooks to prevent future credential commits

---

**Next Step**: Execute Phase 1 (delete unsafe scripts) immediately?

---
*Created: 2026-01-25*  
*Priority: P0 (Security)*
