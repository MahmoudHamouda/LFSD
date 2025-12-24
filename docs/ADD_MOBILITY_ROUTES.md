# How to Add Mobility Routes to app.py

## Quick Instructions

Open `app.py` and make these 2 small changes:

### Change 1: Add Import (Line ~134)

Find this line:
```python
from activity_feed_routes import router as activity_feed_router
```

Add this line RIGHT AFTER it:
```python
from mobility_routes import router as mobility_router
```

### Change 2: Add to Router List (Line ~145)

Find this section:
```python
    for r in [
        audit_router,
        feedback_router,
        chat_router,
        recommendation_router,
        partner_router,
        user_router,
        financial_router,
        notification_router,
        activity_feed_router,
    ]:
```

Add `mobility_router,` to the list (before the closing `]:`):
```python
    for r in [
        audit_router,
        feedback_router,
        chat_router,
        recommendation_router,
        partner_router,
        user_router,
        financial_router,
        notification_router,
        activity_feed_router,
        mobility_router,  # <-- ADD THIS LINE
    ]:
```

### Restart Backend

After making these changes, restart the backend:
1. Stop the current backend (Ctrl+C in the terminal)
2. Run: `python -m uvicorn "app:create_app" --factory --host 0.0.0.0 --port 8002`

## Test the Endpoints

Once restarted, test with:

```bash
# List providers
curl http://localhost:8002/mobility/providers

# Compare prices (Downtown Dubai to Marina)
curl "http://localhost:8002/mobility/compare-prices?start_lat=25.2048&start_lng=55.2708&end_lat=25.1972&end_lng=55.2744"
```

That's it! The mobility integration will be live.
