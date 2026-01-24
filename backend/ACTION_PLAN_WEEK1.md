# 🎯 IMMEDIATE ACTION PLAN - Week 1

**Created**: 2026-01-25  
**Status**: ✅ CODE READY | ⏰ AWAITING EXECUTION  
**Total Time**: ~8-12 hours over 5 days

---

## 🔥 DAY 1: URGENT SECURITY (2 hours)

### ✅ Completed by AI:
- [x] Removed hardcoded API keys from code
- [x] Deleted `models/test_available_models.py`
- [x] Fixed `core/config.py` to require env vars
- [x] Created security audit report
- [x] Scanned repository for other secrets

### 🚨 YOU MUST DO (URGENT):

#### 1. Rotate Both Google Gemini API Keys (30 min)

**Keys to Rotate**:
1. `AIzaSyBTeVnxIK98KHnToQRNWw_HJgsfDHh0pJI` (from test file)
2. `AIzaSyDwhejk-FKUDtA47i5qH4HHGFJEDaX2KBw` (from config)

**Steps**:
```bash
# Go to Google Cloud Console
open https://console.cloud.google.com/apis/credentials

# Find and delete both keys
# Create new API key
# Copy the new key
```

#### 2. Set New Key in Environment (5 min)

Create `backend/.env`:
```bash
# backend/.env
GEMINI_API_KEY=your-new-key-here
ENV=dev
DATABASE_URL=sqlite:///./lfsd_v2.db
```

#### 3. Verify Application Works (15 min)

```bash
cd backend
python -c "from core.config import get_settings; print('✅ Config OK')"

# Start the app
python main.py

# Test a chat endpoint
curl http://localhost:8000/health
```

#### 4. Check Google Cloud Logs (30 min)

```bash
# Look for unauthorized API usage
# Check if old keys were used after exposure
# Document any suspicious activity
```

---

## 📅 DAY 2: Review Documentation (2 hours)

### Priority Reading:

1. **`SECURITY_AUDIT_REPORT.md`** (15 min)  
   - Understand what was exposed
   - Confirm API keys rotated
   
2. **`EXECUTIVE_SUMMARY.md`** (30 min)  
   - Complete overview of changes
   - Architecture before/after
   - Next steps roadmap

3. **`MODELS_FIX_SUMMARY.md`** (30 min)  
   - All model fixes applied
   - 7 anti-patterns explained
   - Breaking changes list

4. **`ALEMBIC_MIGRATION_GUIDE.md`** (45 min)  
   - How to run migrations
   - Complete migration scripts
   - Data cleanup queries

### Takeaways:
- [ ] Understand what changed and why
- [ ] Note any breaking changes
- [ ] Identify models that need migration
- [ ] Plan migration timeline

---

## 🗄️ DAY 3: Database Migrations Setup (3 hours)

### Part 1: Install & Initialize (30 min)

```bash
cd backend

# Install Alembic
pip install alembic

# Initialize
alembic init alembic

# This creates:
# - alembic/
# - alembic.ini
```

### Part 2: Configure Alembic (30 min)

Follow `ALEMBIC_MIGRATION_GUIDE.md`:

1. Edit `alembic/env.py` to import all models
2. Set `target_metadata = Base.metadata`
3. Configure database URL from settings

### Part 3: Backup Database (15 min)

```bash
# PostgreSQL
pg_dump -U postgres -h localhost lfsd > backup_$(date +%Y%m%d).sql

# SQLite (dev)
cp lfsd_v2.db lfsd_v2.db.backup_$(date +%Y%m%d)
```

### Part 4: Create First Migration (1 hour)

```bash
# Auto-generate migration
alembic revision --autogenerate -m "add_model_constraints_and_enums"

# Review generated file
# Edit alembic/versions/xxx_add_model_constraints.py

# Test dry-run
alemb upgrade head --sql > migration.sql
# Review migration.sql
```

### Part 5: Clean Invalid Data (45 min)

Run data cleanup queries from `ALEMBIC_MIGRATION_GUIDE.md`:

```sql
-- Remove duplicates
-- Fix invalid enum values
-- Clamp out-of-bounds scores
-- Fix orphaned FK references
```

---

## ▶️ DAY 4: Run Migrations in Dev (2 hours)

### Step 1: Run Migration (15 min)

```bash
# Run migration
alembic upgrade head

# Verify
alembic current
alembic history
```

### Step 2: Verify Database (30 min)

```sql
-- Check constraints were created
SELECT conname, contype 
FROM pg_constraint 
WHERE conrelid = 'user_scores'::regclass;

-- Check enums were created
SELECT typname FROM pg_type WHERE typtype = 'e';

-- Test a constraint
INSERT INTO user_scores (user_id, financial_score) 
VALUES ('test-user', 150);  -- Should fail!
```

### Step 3: Test Application (1 hour)

```bash
# Start app
python main.py

# Test endpoints
curl http://localhost:8000/api/goals
curl http://localhost:8000/api/health/scores

# Check for errors in logs
tail -f logs/app.log
```

### Step 4: Document Issues (15 min)

```markdown
# Migration Issues Log

## Found:
1. Table X missing column Y
2. Constraint Z failed on existing data

## Resolution:
...
```

---

## 🧪 DAY 5: Final Testing & Staging Deploy (3 hours)

### Part 1: Integration Testing (1 hour)

Test all major flows:
- [ ] User signup/login
- [ ] Create goals
- [ ] View health scores
- [ ] Chat functionality
- [ ] Subscription limits

### Part 2: Performance Check (30 min)

```bash
# Check query performance
EXPLAIN ANALYZE SELECT * FROM health_metrics 
WHERE user_id = 'test' 
ORDER BY timestamp DESC LIMIT 100;

# Verify indexes are used
# Check for slow queries
```

### Part 3: Deploy to Staging (1 hour)

```bash
# Push code
git add .
git commit -m "feat: apply model fixes and migrations"
git push origin main

# Run migrations on staging
ssh staging
cd /app/backend
alembic upgrade head

# Restart services
systemctl restart backend
```

### Part 4: Smoke Test Staging (30 min)

```bash
# Test critical paths
curl https://staging.yourapp.com/health
curl https://staging.yourapp.com/api/users/me

# Check logs
tail -f /var/log/backend/app.log
```

---

## ✅ Success Criteria

By end of Week 1:

- [ ] ✅ API keys rotated and secure
- [ ] ✅ All documentation reviewed
- [ ] ✅ Alembic set up and configured
- [ ] ✅ Migrations created and tested in dev
- [ ] ✅ Application works with new schema
- [ ] ✅ Deployed to staging successfully
- [ ] ✅ No critical bugs found

---

## 📊 Progress Tracking

| Day | Task | Time | Status |
|-----|------|------|--------|
| 1 | Rotate API keys | 2h | ⏳ PENDING |
| 2 | Review docs | 2h | ⏳ PENDING |
| 3 | Setup migrations | 3h | ⏳ PENDING |
| 4 | Run migrations (dev) | 2h | ⏳ PENDING |
| 5 | Test & deploy staging | 3h | ⏳ PENDING |

**Total**: 12 hours over 5 days

---

## 🚨 Blockers & Escalation

### If You Get Stuck:

**Problem**: Alembic installation fails
- **Solution**: Check Python version, use `pip install --upgrade alembic`

**Problem**: Migration has errors
- **Solution**: Review `ALEMBIC_MIGRATION_GUIDE.md`, check data cleanup

**Problem**: Application breaks after migration
- **Solution**: Rollback with `alemb downgrade -1`, restore from backup

**Problem**: Can't rotate API keys
- **Solution**: Check Google Cloud permissions, ask admin

### Need Help?

1. Check relevant documentation file
2. Review error logs carefully
3. Test in isolated environment first
4. Document the issue for future reference

---

## 📚 Reference Documents

| Document | When to Use |
|----------|-------------|
| `SECURITY_AUDIT_REPORT.md` | API key rotation, security issues |
| `EXECUTIVE_SUMMARY.md` | Big picture, what changed overall |
| `MODELS_FIX_SUMMARY.md` | Understanding model changes |
| `ALEMBIC_MIGRATION_GUIDE.md` | Running migrations step-by-step |
| `ROUTES_AUDIT.md` | Security issues in routes (future work) |
| `MASTER_CLEANUP_SUMMARY.md` | Complete transformation details |

---

## 🎯 Week 2 Preview

After Week 1 is complete:

- Week 2: Deploy to production
- Week 2: Add integration tests
- Week 2: Performance optimization
- Week 2: Fix remaining routes issues

---

**Status**: 🎯 **READY TO EXECUTE**  
**Risk**: LOW (with backups and proper testing)  
**Confidence**: VERY HIGH  
**Next Action**: Rotate API keys (Day 1, Task 1)

---

*Created: 2026-01-25*  
*Total Effort: 12 hours over 5 days*  
*Code Status: ✅ Ready*  
*Documentation: ✅ Complete*  
*Your Action: ⏰ Start Day 1*

---

## 🚀 Get Started

```bash
# Day 1, Right Now:
1. Open Google Cloud Console
2. Navigate to API credentials
3. Delete old keys
4. Create new key
5. Save to backend/.env
6. Test application

👉 See "DAY 1: URGENT SECURITY" above for detailed steps
```
