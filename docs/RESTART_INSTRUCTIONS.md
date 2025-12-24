# ========================================
# LFSD Backend Restart Instructions
# ========================================

## The Problem
The backend is already running on port 8002 but doesn't have the new mobility routes loaded.
You need to stop the old one and start a new one.

## Solution - Manual Steps

### Step 1: Stop the Old Backend

**In the terminal where the backend is running:**
1. Press `Ctrl + C` to stop it
2. Wait for it to fully shut down (you'll see "Application shutdown complete")

### Step 2: Start the New Backend

**In the same terminal (or a new one):**
```bash
cd "C:\Users\hmahm\OneDrive\Desktop\LFSD Codebase\LFSD"
python -m uvicorn "app:create_app" --factory --host 0.0.0.0 --port 8002
```

Wait for:
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8002
```

### Step 3: Test It

**In a NEW terminal:**
```bash
cd "C:\Users\hmahm\OneDrive\Desktop\LFSD Codebase\LFSD"
python test_e2e_mobility.py
```

You should see:
```
✅ Success: {'providers': ['uber', 'careem', 'bolt', 'rta']}
Found 11 ride options
💰 Cheapest: Rta RTA Bus (Route 8)  (AED 3.00)
```

## Alternative: Use Task Manager

If Ctrl+C doesn't work:

1. Open Task Manager (Ctrl + Shift + Esc)
2. Find "Python" processes
3. Look for one using ~100MB memory (the backend)
4. Right-click → End Task
5. Then start the backend again (Step 2 above)

## Verify It's Working

Test the mobility endpoint:
```bash
curl http://localhost:8002/mobility/providers
```

Should return:
```json
{"providers": ["uber", "careem", "bolt", "rta"]}
```

## What Changed?

The file `app.py` now includes:
```python
from mobility_routes import router as mobility_router

# And in the router list:
mobility_router,  # <-- NEW!
```

This adds all the mobility endpoints:
- /mobility/providers
- /mobility/compare-prices
- /mobility/cheapest
- /mobility/book-ride
- /mobility/book-cheapest
- /mobility/ride-status/{provider}/{id}

---

**Need Help?** The backend MUST be restarted for the new routes to load!
