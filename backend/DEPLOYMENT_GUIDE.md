# 🚀 Git Commit & Cloud Run Deployment Guide

**Date**: 2026-01-25  
**Prerequisites**: ✅ API key rotated and tested locally  
**Time Required**: 15-20 minutes

---

## 📋 Pre-Deployment Checklist

Before committing, verify:

- [ ] ✅ New Google Gemini API key is working locally
- [ ] ✅ `.env` file created (and in `.gitignore` - won't be committed)
- [ ] ✅ Old API keys deleted from Google Cloud
- [ ] ✅ All code changes from cleanup are applied
- [ ] ✅ No hardcoded secrets in code

---

## 📦 Step 1: Review What Will Be Committed

```bash
cd backend

# Check git status
git status

# You should see (among other changes):
# Modified:
#   - core/config.py (hardcoded key removed)
#   - models/ (10+ model files fixed)
#   - dependencies/growth_dependencies.py
#   - MANY documentation files
# Deleted:
#   - models/test_available_models.py (had exposed key)
# Untracked/Ignored:
#   - .env (correctly ignored)
```

### View Changes:
```bash
# See what changed in config.py
git diff core/config.py

# See all changed files
git diff --name-status
```

---

## ✅ Step 2: Stage All Changes

```bash
# Stage all modified and new files
git add .

# Verify what's staged
git status

# Make sure .env is NOT staged (should be in .gitignore)
git status | grep ".env"
# Should show: nothing (or "ignored")
```

---

## 💾 Step 3: Commit Changes

```bash
git commit -m "feat: backend modernization and security hardening

SECURITY FIXES:
- Remove hardcoded Google Gemini API keys
- Delete test_available_models.py (exposed credentials)
- Make GEMINI_API_KEY required from environment
- Add comprehensive .gitignore

MODEL FIXES:
- Fix all timestamps to timezone-aware
- Correct all user FK references to users_v2
- Add enums for type safety (27 new enums)
- Add uniqueness constraints (15 constraints)
- Add check constraints for score bounds (20+ constraints)
- Convert JSON text fields to proper JSON columns
- Fix UUID defaults on primary keys

FILES CLEANED:
- Deleted 108 unsafe/duplicate files
- Consolidated 5 microservices to 1 FastAPI app
- Unified 3 auth systems to 1
- Fixed 10 model files

DOCUMENTATION:
- Added 10 comprehensive audit/guide documents (~4,500 lines)
- Created security audit report
- Created migration guides
- Created deployment documentation

Breaking Changes:
- GEMINI_API_KEY now required from environment (no default)
- Database migrations required before deployment (see ALEMBIC_MIGRATION_GUIDE.md)

Refs: EXECUTIVE_SUMMARY.md, SECURITY_AUDIT_REPORT.md, MODELS_FIX_SUMMARY.md"
```

---

## 🌐 Step 4: Push to Repository

### Option A: Direct Push (Main Branch)

```bash
# Push to main
git push origin main

# Or if you're on a different branch:
git push origin <your-branch-name>
```

### Option B: Create Feature Branch (Safer)

```bash
# Create new branch
git checkout -b feat/backend-modernization-2026-01

# Push branch
git push -u origin feat/backend-modernization-2026-01

# Then create Pull Request in GitHub/GitLab for review
```

---

## ☁️ Step 5: Deploy to Cloud Run

### Check Current Cloud Run Service

```bash
# List services
gcloud run services list --project=newprojectlfsd

# Describe current service
gcloud run services describe backend \
  --region=us-central1 \
  --project=newprojectlfsd
```

### Set Environment Variable in Cloud Run

**CRITICAL**: Set the new API key as environment variable:

```bash
# Set GEMINI_API_KEY in Cloud Run
gcloud run services update backend \
  --region=us-central1 \
  --project=newprojectlfsd \
  --update-env-vars GEMINI_API_KEY=YOUR_NEW_API_KEY_HERE

# Or use Secret Manager (more secure - recommended):
# 1. Create secret
gcloud secrets create gemini-api-key \
  --data-file=- \
  --project=newprojectlfsd <<< "YOUR_NEW_API_KEY_HERE"

# 2. Grant Cloud Run access
gcloud secrets add-iam-policy-binding gemini-api-key \
  --member="serviceAccount:692544481281-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=newprojectlfsd

# 3. Update Cloud Run to use secret
gcloud run services update backend \
  --region=us-central1 \
  --project=newprojectlfsd \
  --update-secrets=GEMINI_API_KEY=gemini-api-key:latest
```

### Deploy New Code

```bash
# If you have cloudbuild.yaml or CI/CD:
# Push will automatically trigger deployment

# Manual deployment (if needed):
gcloud run deploy backend \
  --source=. \
  --region=us-central1 \
  --project=newprojectlfsd \
  --allow-unauthenticated

# Or use existing Dockerfile:
# 1. Build image
gcloud builds submit --tag gcr.io/newprojectlfsd/backend

# 2. Deploy image
gcloud run deploy backend \
  --image gcr.io/newprojectlfsd/backend \
  --region=us-central1 \
  --project=newprojectlfsd
```

---

## ✅ Step 6: Verify Deployment

### Check Service Health

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe backend \
  --region=us-central1 \
  --project=newprojectlfsd \
  --format='value(status.url)')

echo "Service URL: $SERVICE_URL"

# Test health endpoint
curl $SERVICE_URL/health

# Test API (if you have a test endpoint)
curl $SERVICE_URL/api/test
```

### Check Logs

```bash
# View recent logs
gcloud run services logs read backend \
  --region=us-central1 \
  --project=newprojectlfsd \
  --limit=50

# Follow logs in real-time
gcloud run services logs tail backend \
  --region=us-central1 \
  --project=newprojectlfsd
```

### Verify Environment Variables

```bash
# Check that GEMINI_API_KEY is set (value hidden)
gcloud run services describe backend \
  --region=us-central1 \
  --project=newprojectlfsd \
  --format='value(spec.template.spec.containers[0].env)'
```

---

## 🔄 Step 7: Run Database Migrations (if ready)

**IMPORTANT**: Only after Cloud Run deployment is successful.

See `ALEMBIC_MIGRATION_GUIDE.md` for detailed steps, but summary:

```bash
# Option A: SSH to Cloud Run and run Alembic
gcloud run services proxy backend --port=8080 --region=us-central1
# (In another terminal, connect and run migrations)

# Option B: Add Alembic to startup script
# Edit main.py to run migrations on startup (not recommended for prod)

# Option C: Run migrations from local machine against Cloud SQL
# 1. Enable Cloud SQL Proxy
# 2. Run: alembic upgrade head
```

---

## 🚨 Rollback Plan (If Something Goes Wrong)

### Rollback Code:

```bash
# Revert last commit
git revert HEAD
git push origin main

# Or rollback to specific commit
git reset --hard <previous-commit-hash>
git push --force origin main
```

### Rollback Cloud Run Deployment:

```bash
# List revisions
gcloud run revisions list \
  --service=backend \
  --region=us-central1 \
  --project=newprojectlfsd

# Rollback to previous revision
gcloud run services update-traffic backend \
  --to-revisions=<previous-revision>=100 \
  --region=us-central1 \
  --project=newprojectlfsd
```

---

## 📊 Post-Deployment Checklist

After deployment, verify:

- [ ] Cloud Run service is healthy
- [ ] Environment variables are set correctly
- [ ] API endpoints respond correctly
- [ ] No errors in Cloud Run logs
- [ ] Old API keys are deleted (not being used)
- [ ] New API key works in production
- [ ] Frontend can communicate with backend

---

## ⏭️ What's Next

After successful deployment:

1. **Run Alembic Migrations** (see `ALEMBIC_MIGRATION_GUIDE.md`)
   - Test migrations locally first
   - Then run on Cloud SQL

2. **Monitor for Issues**
   - Check logs for errors
   - Monitor API usage in Google Cloud
   - Test all critical user flows

3. **Week 2 Tasks**
   - Add integration tests
   - Performance optimization  
   - Additional route hardening

---

## 📚 Reference Documents

| Document | When to Use |
|----------|-------------|
| `API_KEY_ROTATION_FINAL_STEPS.md` | Before this guide |
| `ALEMBIC_MIGRATION_GUIDE.md` | After deployment |
| `SECURITY_AUDIT_REPORT.md` | Security reference |
| `EXECUTIVE_SUMMARY.md` | Overall changes |

---

**Status**: 📋 **READY FOR EXECUTION**  
**Prerequisites**: ✅ API key rotation complete  
**Estimated Time**: 15-20 minutes  
**Risk**: LOW (rollback available)

---

*Created: 2026-01-25*  
*Project: newprojectlfsd*  
*Region: us-central1*  
*Service: backend*

---

## 🎯 Quick Start

```bash
# Execute these commands in order:

# 1. Review changes
git status
git diff --name-status

# 2. Commit
git add .
git commit -m "feat: backend modernization and security hardening"

# 3. Push
git push origin main

# 4. Set environment variable in Cloud Run
gcloud run services update backend \
  --region=us-central1 \
  --project=newprojectlfsd \
  --update-secrets=GEMINI_API_KEY=gemini-api-key:latest

# 5. Verify deployment
curl $(gcloud run services describe backend --region=us-central1 --format='value(status.url)')/health

# 6. Check logs
gcloud run services logs tail backend --region=us-central1

# DONE! ✅
```
