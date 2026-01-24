# ✅ COMPLETE EXECUTION CHECKLIST

**Created**: 2026-01-25  
**Status**: 📋 YOUR ACTION REQUIRED  
**Total Phases**: 3  
**Estimated Time**: 2-3 hours total

---

## 🎯 **PHASE 1: API Key Rotation** (15 min) ⏳ IN PROGRESS

### Step 1.1: Retrieve New API Key ⏳ NEXT

**What**: Get the new Google Gemini API key I created for you

**How**: Follow `API_KEY_ROTATION_FINAL_STEPS.md`

**Quick Steps**:
```bash
# Open Google Cloud Console
https://console.cloud.google.com/apis/credentials?project=newprojectlfsd

# Find: "LFSD Backend - Rotated 2026-01-25"
# Click "SHOW KEY"
# Copy the key
```

**Checklist**:
- [ ] Opened Google Cloud Console
- [ ] Found new API key
- [ ] Copied key value

---

### Step 1.2: Create .env File (2 min)

**What**: Store the new API key locally for development

**How**:
```bash
cd backend

# Copy template
cp .env.template .env

# Edit .env and replace YOUR_NEW_KEY_HERE with actual key
```

**Your .env file should contain**:
```bash
ENV=dev
DATABASE_URL=sqlite:///./lfsd_v2.db
GEMINI_API_KEY=AIzaSy[your-actual-new-key-here]
```

**Checklist**:
- [ ] Created `.env` file
- [ ] Added new API key
- [ ] Verified `.env` is in `.gitignore` (won't be committed)

---

### Step 1.3: Delete Old Keys (3 min)

**What**: Remove the compromised API keys from Google Cloud

**How**:
```bash
# List all keys
gcloud services api-keys list --project=newprojectlfsd

# Delete old keys (NOT the "Rotated 2026-01-25" one)
# For each old key:
gcloud services api-keys delete [KEY_PATH] --project=newprojectlfsd
```

**Checklist**:
- [ ] Listed all API keys  
- [ ] Identified old keys to delete
- [ ] Deleted all old keys
- [ ] Verified only new key remains

---

### Step 1.4: Test Locally (2 min)

**What**: Verify the new API key works

**How**:
```bash
cd backend

# Test config loading
python -c "from core.config import get_settings; print('✅ Key loaded:', get_settings().GEMINI_API_KEY[:20] + '...')"

# Should print: ✅ Key loaded: AIzaSy...
```

**Checklist**:
- [ ] Config loads without errors
- [ ] API key is correctly loaded
- [ ] No hardcoded key warnings

**✅ PHASE 1 COMPLETE** when all checkboxes above are checked.

---

## 📦 **PHASE 2: Git Commit & Deploy** (20 min) ⏳ AFTER PHASE 1

### Step 2.1: Review Changes (5 min)

**What**: Understand what will be committed

**How**: Follow `DEPLOYMENT_GUIDE.md` Section "Step 1"

```bash
cd backend

# Check status
git status

# View changes
git diff --name-status
```

**Checklist**:
- [ ] Reviewed `git status` output
- [ ] Verified no secrets in staged files
- [ ] Confirmed `.env` is NOT staged

---

### Step 2.2: Commit Changes (3 min)

**What**: Commit all the modernization work

**How**:
```bash
git add .

git commit -m "feat: backend modernization and security hardening

[Full commit message in DEPLOYMENT_GUIDE.md]"
```

**Checklist**:
- [ ] All changes staged
- [ ] Commit created
- [ ] Commit message includes security fixes

---

### Step 2.3: Push to Repository (2 min)

**What**: Push code to GitHub/GitLab

**How**:
```bash
git push origin main
```

**Checklist**:
- [ ] Code pushed successfully
- [ ] No errors during push
- [ ] Changes visible in remote repository

---

### Step 2.4: Set API Key in Cloud Run (5 min)

**What**: Configure Cloud Run with the new API key

**How**: Use Secret Manager (recommended)

```bash
# 1. Create secret
gcloud secrets create gemini-api-key \
  --data-file=- \
  --project=newprojectlfsd <<< "YOUR_NEW_API_KEY"

# 2. Grant access
gcloud secrets add-iam-policy-binding gemini-api-key \
  --member="serviceAccount:692544481281-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=newprojectlfsd

# 3. Update Cloud Run
gcloud run services update backend \
  --region=us-central1 \
  --project=newprojectlfsd \
  --update-secrets=GEMINI_API_KEY=gemini-api-key:latest
```

**Checklist**:
- [ ] Secret created in Secret Manager
- [ ] Cloud Run has access to secret
- [ ] Service updated with secret reference

---

### Step 2.5: Deploy Code (3 min)

**What**: Deploy new code to Cloud Run

**How**:
```bash
# If auto-deploy is set up, this happens automatically after push

# Manual deploy (if needed):
gcloud run deploy backend \
  --source=. \
  --region=us-central1 \
  --project=newprojectlfsd
```

**Checklist**:
- [ ] Deployment initiated
- [ ] Deployment completed successfully
- [ ] New revision is serving traffic

---

### Step 2.6: Verify Deployment (2 min)

**What**: Confirm Cloud Run is healthy

**How**:
```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe backend \
  --region=us-central1 \
  --project=newprojectlfsd \
  --format='value(status.url)')

# Test health
curl $SERVICE_URL/health

# Check logs
gcloud run services logs read backend \
  --region=us-central1 \
  --limit=20
```

**Checklist**:
- [ ] Health endpoint responds
- [ ] No errors in logs
- [ ] Service is accessible

**✅ PHASE 2 COMPLETE** when all checkboxes above checked.

---

## 🗄️ **PHASE 3: Database Migrations** (1-2 hours) ⏳ AFTER PHASE 2

### Step 3.1: Install Alembic Locally (5 min)

**What**: Set up migration tooling

**How**:
```bash
cd backend
pip install alembic
alembic init alembic
```

**Checklist**:
- [ ] Alembic installed
- [ ] `alembic/` folder created
- [ ] `alembic.ini` file created

---

### Step 3.2: Configure Alembic (15 min)

**What**: Point Alembic to your models

**How**: Follow `ALEMBIC_MIGRATION_GUIDE.md` Section "Part 1"

**Checklist**:
- [ ] Edited `alembic/env.py` to import all models
- [ ] Set `target_metadata = Base.metadata`
- [ ] Configured database URL

---

### Step 3.3: Create Migrations (30 min)

**What**: Generate migration files

**How**:
```bash
# Auto-generate
alembic revision --autogenerate -m "add_model_constraints_and_enums"

# Review generated file
# Edit alembic/versions/xxx_add_model_constraints.py

# Test SQL generation
alembic upgrade head --sql > test_migration.sql
```

**Checklist** - [ ] Migration file generated
- [ ] Reviewed migration content
- [ ] SQL looks correct

---

### Step 3.4: Clean Invalid Data (20 min)

**What**: Fix existing data that violates new constraints

**How**: Run SQL queries from `ALEMBIC_MIGRATION_GUIDE.md` Section "Part 3"

```sql
-- Remove duplicates
-- Fix invalid enum values
-- Clamp out-of-bounds scores
```

**Checklist**:
- [ ] Duplicates removed
- [ ] Invalid enums fixed
- [ ] Scores clamped to bounds

---

### Step 3.5: Run Migrations Locally (10 min)

**What**: Test migrations on local SQLite

**How**:
```bash
# Run migration
alembic upgrade head

# Verify
alembic current
```

**Checklist**:
- [ ] Migration ran without errors
- [ ] Database schema updated
- [ ] Application still works locally

---

### Step 3.6: Run Migrations on Cloud SQL (20 min)

**What**: Apply migrations to production database

**How**:
```bash
# Option A: Connect to Cloud SQL via proxy
cloud_sql_proxy -instances=newprojectlfsd:us-central1:lfsd=tcp:5432

# In another terminal:
export DATABASE_URL="postgresql://user:pass@localhost:5432/lfsd"
alembic upgrade head

# Option B: Run from Cloud Run instance
# (Add migration command to startup script)
```

**Checklist**:
- [ ] Connected to Cloud SQL
- [ ] Migration ran successfully
- [ ] Schema updated in production
- [ ] Application tested after migration

**✅ PHASE 3 COMPLETE** when all checkboxes checked.

---

## 🎉 **FINAL VERIFICATION**

After all 3 phases complete:

### Functionality Tests:
- [ ] User can sign up/login
- [ ] Goals can be created
- [ ] Health scores display
- [ ] Chat works
- [ ] No 500 errors

### Security Tests:
- [ ] Old API keys deleted
- [ ] New API key works
- [ ] No secrets in git repo
- [ ] Environment variables set correctly

### Performance Tests:
- [ ] App responds quickly
- [ ] No database errors
- [ ] Logs are clean

---

## 📊 Progress Tracking

| Phase | Tasks | Time | Status |
|-------|-------|------|--------|
| **1. API Key Rotation** | 4 steps | 15 min | ⏳ IN PROGRESS |
| **2. Git & Deploy** | 6 steps | 20 min | ⏳ WAITING |
| **3. DB Migrations** | 6 steps | 1-2 hours | ⏳ WAITING |

**Total Progress**: 0% → 100% when all complete

---

## 🚨 If You Get Stuck

### Problem: Can't find new API key
**Solution**: See `API_KEY_ROTATION_FINAL_STEPS.md`

### Problem: Git push fails
**Solution**: Check remote repository access, pull latest changes first

### Problem: Cloud Run deployment fails
**Solution**: Check `gcloud run services logs`, verify Dockerfile

### Problem: Migration has errors
**Solution**: Check `ALEMBIC_MIGRATION_GUIDE.md`, run data cleanup first

---

## 📚 Quick Reference

| Step | Document | Time |
|------|----------|------|
| Get API key | `API_KEY_ROTATION_FINAL_STEPS.md` | 5 min |
| Git & Deploy | `DEPLOYMENT_GUIDE.md` | 20 min |
| Migrations | `ALEMBIC_MIGRATION_GUIDE.md` | 1-2 hrs |
| Overview | `EXECUTIVE_SUMMARY.md` | Read anytime |
| Security | `SECURITY_AUDIT_REPORT.md` | Reference |

---

## ✅ **What Success Looks Like**

When you're done:

1. ✅ New API key is active and old ones deleted
2. ✅ Code is committed and deployed to Cloud Run
3. ✅ Database has all new constraints and enums
4. ✅ Application works end-to-end
5. ✅ No security vulnerabilities
6. ✅ Production-ready backend

---

**Status**: 📋 **START WITH PHASE 1**  
**First Action**: Open `API_KEY_ROTATION_FINAL_STEPS.md`  
**Completion ETA**: 2-3 hours total  
**Current Step**: ⏳ Retrieve new API key from Google Cloud Console

---

*Created: 2026-01-25*  
*Total Steps: 16*  
*Completed: 0*  
*Remaining: 16*

---

## 🚀 **START HERE**

```bash
# Step 1: Open Google Cloud Console
https://console.cloud.google.com/apis/credentials?project=newprojectlfsd

# Find key: "LFSD Backend - Rotated 2026-01-25"
# Click "SHOW KEY"
# Copy it

# Then open: API_KEY_ROTATION_FINAL_STEPS.md
```
