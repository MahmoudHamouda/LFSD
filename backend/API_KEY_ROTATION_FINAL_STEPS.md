# 🔐 API Key Rotation - Final Steps (YOU DO THIS)

**Date**: 2026-01-25  
**Status**: ✅ New key created | ⏳ YOU must retrieve and set it

---

## ✅ What I've Done (Automated)

1. ✅ Created new API key: "LFSD Backend - Rotated 2026-01-25"
2. ✅ Verified project: `newprojectlfsd`
3. ✅ Removed hardcoded keys from code
4. ✅ Created `.env.template` file

---

## 🎯 **What YOU Must Do Now** (5 minutes)

### Step 1: Get the New API Key (2 min)

**Option A: Google Cloud Console** (Easiest):
```bash
# Open this URL:
https://console.cloud.google.com/apis/credentials?project=newprojectlfsd

# Find key: "LFSD Backend - Rotated 2026-01-25"
# Click "SHOW KEY" button
# Copy the key (starts with AIzaSy...)
```

**Option B: gcloud CLI**:
```bash
# List all keys with their values
gcloud services api-keys list \
  --project=newprojectlfsd \
  --format="value(displayName,keyString)" \
  | grep "LFSD Backend - Rotated"

# Copy the key value
```

### Step 2: Create .env File (1 min)

```bash
cd backend

# Copy template
cp .env.template .env

# Edit .env file and replace YOUR_NEW_KEY_HERE with actual key
# File: backend/.env
```

**Your .env should look like**:
```bash
ENV=dev
DATABASE_URL=sqlite:///./lfsd_v2.db
GEMINI_API_KEY=AIzaSy___YOUR_ACTUAL_NEW_KEY___
```

### Step 3: Delete Old Keys (1 min)

```bash
# List all keys
gcloud services api-keys list --project=newprojectlfsd

# Delete the old keys (find their IDs from the list)
# Look for keys that are NOT "LFSD Backend - Rotated 2026-01-25"

# Delete each old key:
gcloud services api-keys delete projects/692544481281/locations/global/keys/[OLD_KEY_ID] \
  --project=newprojectlfsd
```

### Step 4: Test Locally (1 min)

```bash
cd backend

# Verify config loads
python -c "from core.config import get_settings; print('✅ Key loaded:', get_settings().GEMINI_API_KEY[:20] + '...')"

# Should print:
# ✅ Key loaded: AIzaSy...
```

---

## 📊 Verification Checklist

Before proceeding to git commit:

- [ ] New API key retrieved from Google Cloud Console
- [ ] `.env` file created with new key
- [ ] Old API keys deleted from Google Cloud
- [ ] Application tested locally with new key
- [ ] No errors when loading config

---

## ⏭️ Next: Git Commit & Push

Once verification is complete, run:

```bash
# See DEPLOYMENT_GUIDE.md for next steps
```

---

**Status**: ⏳ WAITING FOR YOU  
**Next Document**: `DEPLOYMENT_GUIDE.md` (will create after you confirm key works)  
**ETA**: 5 minutes

---

*Created: 2026-01-25*  
*Project: newprojectlfsd*  
*New Key Name: LFSD Backend - Rotated 2026-01-25*
