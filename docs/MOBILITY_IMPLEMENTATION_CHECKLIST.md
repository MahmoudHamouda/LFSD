# Mobility Integration - Implementation Checklist

## ✅ What You Already Have (Great News!)

Your codebase is already well-prepared for mobility integrations:

- ✅ **Database Models**: `DBInteraction`, `DBPriceHistory`, `DBConnection`, `DBOrder` (in `models.py`)
- ✅ **Service Pattern**: `uber_service.py` as a reference implementation
- ✅ **API Structure**: FastAPI with route modules
- ✅ **Authentication**: User auth system in place
- ✅ **AI Integration**: Gemini service ready to enhance

## 📋 Phase 1: Foundation Setup (Start Here!)

### Step 1.1: Create Directory Structure
```bash
mkdir -p services/mobility
touch services/mobility/__init__.py
```

### Step 1.2: Create Base Service Class
**File**: `services/mobility/base_mobility_service.py`
- [ ] Define abstract interface
- [ ] Implement common logging methods
- [ ] Add price formatting utilities

### Step 1.3: Refactor Existing Uber Service
**File**: `services/mobility/uber_service.py`
- [ ] Move from `services/uber_service.py` to `services/mobility/uber_service.py`
- [ ] Extend `BaseMobilityService`
- [ ] Keep existing functionality intact

### Step 1.4: Create Mobility Aggregator
**File**: `services/mobility/mobility_aggregator.py`
- [ ] Initialize all provider services
- [ ] Implement `compare_prices()` method
- [ ] Implement `book_cheapest_ride()` method

### Step 1.5: Create API Routes
**File**: `mobility_routes.py`
- [ ] `/mobility/compare-prices` endpoint
- [ ] `/mobility/book-ride` endpoint
- [ ] `/mobility/ride-status/{provider}/{ride_id}` endpoint
- [ ] Register routes in `app.py`

## 📋 Phase 2: Careem Integration

### Step 2.1: API Setup
- [ ] Obtain Careem API credentials
- [ ] Add to `.env`: `CAREEM_API_KEY`, `CAREEM_API_SECRET`
- [ ] Update `config.py` with Careem settings

### Step 2.2: Implement Careem Service
**File**: `services/mobility/careem_service.py`
- [ ] Extend `BaseMobilityService`
- [ ] Implement `get_price_estimates()`
- [ ] Implement `book_ride()`
- [ ] Implement `get_ride_status()`
- [ ] Add Careem-specific features (packages, subscriptions)

### Step 2.3: Test Careem Integration
- [ ] Unit tests for Careem service
- [ ] Integration test with real API
- [ ] Test price comparison Uber vs Careem
- [ ] Test booking flow

## 📋 Phase 3: Bolt Integration

### Step 3.1: API Setup
- [ ] Obtain Bolt API credentials
- [ ] Add to `.env`: `BOLT_API_KEY`
- [ ] Update `config.py`

### Step 3.2: Implement Bolt Service
**File**: `services/mobility/bolt_service.py`
- [ ] Extend `BaseMobilityService`
- [ ] Implement required methods
- [ ] Handle Bolt-specific response formats

### Step 3.3: Test Multi-Provider Comparison
- [ ] Test 3-way price comparison (Uber, Careem, Bolt)
- [ ] Verify sorting by price
- [ ] Test booking with each provider

## 📋 Phase 4: RTA (Public Transport) Integration

### Step 4.1: API Setup
- [ ] Obtain RTA API credentials
- [ ] Add to `.env`: `RTA_API_KEY`

### Step 4.2: Implement RTA Service
**File**: `services/mobility/rta_service.py`
- [ ] Implement `get_transit_routes()`
- [ ] Implement `get_metro_schedule()`
- [ ] Implement `get_bus_schedule()`
- [ ] Add station/stop lookup

### Step 4.3: Integrate with Ride Services
- [ ] Show public transit + ride options together
- [ ] Calculate "last mile" ride costs
- [ ] Suggest hybrid routes (metro + Uber)

## 📋 Phase 5: AI Enhancement (Gemini Integration)

### Step 5.1: Update Gemini Service
**File**: `services/gemini_service.py`
- [ ] Import `MobilityAggregator`
- [ ] Add mobility intent detection
- [ ] Implement location extraction from natural language
- [ ] Add context-aware recommendations

### Step 5.2: Conversation Flow Examples
```
User: "How much to get from Downtown to Marina?"
AI: Detects locations → Calls mobility.compare_prices() → Formats response

User: "Book the cheapest option"
AI: Calls mobility.book_cheapest_ride() → Confirms booking

User: "What's the status of my ride?"
AI: Calls mobility.get_ride_status() → Shows real-time updates
```

### Step 5.3: Smart Features
- [ ] Price alerts (notify when prices drop)
- [ ] Route suggestions based on time of day
- [ ] Favorite locations (home, work)
- [ ] Recurring trip patterns

## 📋 Phase 6: Analytics & Insights

### Step 6.1: Create Analytics Queries
**File**: `services/mobility/analytics.py`
- [ ] Most used provider per user
- [ ] Price trends over time
- [ ] Popular routes
- [ ] Cost savings from comparison

### Step 6.2: Dashboard Endpoints
**File**: `analytics_routes.py` (update existing)
- [ ] `/analytics/mobility/usage`
- [ ] `/analytics/mobility/savings`
- [ ] `/analytics/mobility/trends`

## 🔧 Quick Start Commands

```bash
# 1. Create directory structure
cd services
mkdir mobility
cd mobility
touch __init__.py base_mobility_service.py mobility_aggregator.py

# 2. Move Uber service
mv ../uber_service.py ./uber_service.py

# 3. Create new provider services
touch careem_service.py bolt_service.py rta_service.py

# 4. Create routes
cd ../..
touch mobility_routes.py

# 5. Update app.py to include new routes
# Add: from mobility_routes import router as mobility_router
# Add: app.include_router(mobility_router)
```

## 📊 Database Queries for Tracking

### Track Price Checks
```sql
SELECT 
    provider,
    COUNT(*) as checks,
    DATE(timestamp) as date
FROM interactions
WHERE interaction_type = 'price_check'
GROUP BY provider, DATE(timestamp)
ORDER BY date DESC, checks DESC;
```

### Track Bookings
```sql
SELECT 
    partner as provider,
    status,
    COUNT(*) as count
FROM orders
GROUP BY partner, status;
```

### Calculate Savings
```sql
-- Compare prices user paid vs. cheapest available
SELECT 
    user_id,
    SUM(
        (SELECT MIN(price_estimate) 
         FROM price_history ph2 
         WHERE ph2.timestamp BETWEEN ph1.timestamp - INTERVAL '5 minutes' 
           AND ph1.timestamp + INTERVAL '5 minutes'
           AND ph2.start_location = ph1.start_location
           AND ph2.end_location = ph1.end_location
        ) - ph1.price_estimate
    ) as potential_savings
FROM price_history ph1
JOIN orders o ON o.user_id = ph1.user_id
GROUP BY user_id;
```

## 🎯 Success Metrics

Track these KPIs:
- [ ] Number of price comparisons per day
- [ ] Conversion rate (comparisons → bookings)
- [ ] Average savings per booking
- [ ] Provider market share
- [ ] User retention (repeat users)
- [ ] API response times
- [ ] Error rates per provider

## 🚀 Ready to Start?

**Recommended First Steps:**
1. Review the architecture document: `docs/MOBILITY_INTEGRATION_ARCHITECTURE.md`
2. Create the `services/mobility/` directory
3. Implement `base_mobility_service.py`
4. Refactor `uber_service.py` to use the base class
5. Test the refactored Uber service
6. Then proceed to Careem integration

**Questions to Answer Before Starting:**
- Which provider should we prioritize first? (Careem recommended for UAE market)
- Do you have API credentials for any providers yet?
- What's the target timeline for Phase 1?
- Should we implement mock services first for testing?
