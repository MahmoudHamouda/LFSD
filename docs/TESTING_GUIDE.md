# LFSD Frontend + Backend Testing Guide

## Quick Start

### 1. Database Migration
```bash
cd "c:\Users\hmahm\OneDrive\Desktop\LFSD Codebase\LFSD"
python migrate_health_tables.py
```

### 2. Start Backend Server
```bash
python -m uvicorn app:create_app --factory --port 8002 --reload
```

### 3. Start Frontend Dev Server
```bash
cd frontend
npm run dev
```

### 4. Test API Endpoints
```bash
python test_api_endpoints.py
```

---

## Manual Testing Checklist

### Backend API Tests

#### Health Check
```bash
curl http://localhost:8002/healthz
```

#### Get User Data
```bash
curl http://localhost:8002/api/user/me
```

#### Get Health Connections
```bash
curl http://localhost:8002/api/health/connections
```

#### Connect Health Provider
```bash
curl -X POST http://localhost:8002/api/health/connections \
  -H "Content-Type: application/json" \
  -d "{\"provider\":\"whoop\",\"permissions\":[\"sleep\",\"recovery\",\"activity\"]}"
```

#### Get Unified History
```bash
curl -X POST http://localhost:8002/api/history/unified \
  -H "Content-Type: application/json" \
  -d "{\"filters\":{\"types\":[],\"category\":\"all\"},\"limit\":10}"
```

#### Calculate Indexes
```bash
curl -X POST http://localhost:8002/api/indexes/calculate
```

#### Get Current Indexes
```bash
curl http://localhost:8002/api/indexes/current
```

---

## Frontend Journey Tests

### Home Page Journey
1. Navigate to `http://localhost:5173/`
2. Verify SummaryIndexBar displays with 3 indexes
3. Check Today's Highlights section shows 3 cards
4. Verify Quick Actions grid has 4 buttons
5. Check Smart Recommendations section displays
6. Verify Streaks section appears

### History Page Journey
1. Navigate to `http://localhost:5173/history`
2. Verify SummaryIndexBar appears (compact mode)
3. Check filter chips are clickable
4. Verify date range filters work
5. Check timeline displays grouped items
6. Verify clicking items shows details

### Health Dashboard Journey
1. Navigate to `http://localhost:5173/health`
2. If no connections: verify empty state with "Connect" button
3. If connected: verify metrics cards display
4. Check connection status cards
5. Verify insights section appears

### Health Connect Journey
1. Navigate to `http://localhost:5173/health/connect`
2. Verify 3 provider cards (WHOOP, Apple Health, Android Health)
3. Check "Connect" buttons are functional
4. Verify benefits list displays for each provider
5. Check Privacy & Security section at bottom

---

## Expected Results

### API Endpoints
- ✅ `/healthz` returns `{"status": "ok"}`
- ✅ `/api/user/me` returns complete user object
- ✅ `/api/health/connections` returns connections array
- ✅ `/api/health/connections` (POST) creates connection
- ✅ `/api/history/unified` returns grouped history
- ✅ `/api/indexes/calculate` calculates and returns indexes
- ✅ `/api/indexes/current` returns latest indexes

### Frontend Pages
- ✅ Home page displays indexes and highlights
- ✅ History page shows unified timeline
- ✅ Health dashboard shows metrics or empty state
- ✅ Health connect allows provider management

---

## Troubleshooting

### Backend Issues
- **Port already in use**: Kill process on port 8002
- **Module not found**: Run `pip install -r requirements.txt`
- **Database errors**: Check SQLite database file exists

### Frontend Issues
- **React Query errors**: Verify backend is running
- **Type errors**: Run `npm install` to ensure dependencies
- **Routing issues**: Clear browser cache

---

## Notes

- Backend runs on `http://localhost:8002`
- Frontend runs on `http://localhost:5173` (Vite default)
- Database: SQLite (`lfsd.db`)
- Default user ID: `default_user`
