# Mobility Integration - Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React)                                │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Chat UI      │  │ Price Compare│  │ Ride Booking │  │ Ride Tracking│   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│         │                 │                 │                 │            │
└─────────┼─────────────────┼─────────────────┼─────────────────┼────────────┘
          │                 │                 │                 │
          │                 │                 │                 │
          ▼                 ▼                 ▼                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          BACKEND API (FastAPI)                               │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         API ROUTES LAYER                              │  │
│  │                                                                        │  │
│  │  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐                │  │
│  │  │history_routes│  │mobility_routes│  │analytics_routes│               │  │
│  │  │             │  │              │  │              │                │  │
│  │  │ /generate   │  │ /compare     │  │ /usage       │                │  │
│  │  │ /read       │  │ /book        │  │ /savings     │                │  │
│  │  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘                │  │
│  └─────────┼────────────────┼──────────────────┼────────────────────────┘  │
│            │                │                  │                            │
│            ▼                ▼                  ▼                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      SERVICE LAYER                                   │   │
│  │                                                                       │   │
│  │  ┌──────────────────┐         ┌────────────────────────────────┐    │   │
│  │  │ GeminiService    │◄────────┤  MobilityAggregator            │    │   │
│  │  │                  │         │                                │    │   │
│  │  │ - AI Chat        │         │  ┌──────────────────────────┐ │    │   │
│  │  │ - Intent Detect  │         │  │ BaseMobilityService      │ │    │   │
│  │  │ - Location Extract│        │  │ (Abstract Interface)     │ │    │   │
│  │  └──────────────────┘         │  └────────────┬─────────────┘ │    │   │
│  │                               │               │               │    │   │
│  │                               │  ┌────────────▼──────────┐    │    │   │
│  │                               │  │                       │    │    │   │
│  │                               │  ├─ UberService         │    │    │   │
│  │                               │  │  • get_price_estimates│    │    │   │
│  │                               │  │  • book_ride          │    │    │   │
│  │                               │  │  • get_ride_status    │    │    │   │
│  │                               │  │  • log_interaction    │    │    │   │
│  │                               │  │                       │    │    │   │
│  │                               │  ├─ CareemService        │    │    │   │
│  │                               │  │  • get_price_estimates│    │    │   │
│  │                               │  │  • book_ride          │    │    │   │
│  │                               │  │  • get_packages       │    │    │   │
│  │                               │  │                       │    │    │   │
│  │                               │  ├─ BoltService          │    │    │   │
│  │                               │  │  • get_price_estimates│    │    │   │
│  │                               │  │  • book_ride          │    │    │   │
│  │                               │  │                       │    │    │   │
│  │                               │  └─ RTAService           │    │    │   │
│  │                               │    • get_transit_routes  │    │    │   │
│  │                               │    • get_metro_schedule  │    │    │   │
│  │                               │    • get_bus_schedule    │    │    │   │
│  │                               │                          │    │    │   │
│  │                               └──────────────────────────┘    │    │   │
│  └───────────────────────────────────────────────────────────────┘    │   │
│                                      │                                 │   │
│                                      ▼                                 │   │
│  ┌─────────────────────────────────────────────────────────────────┐  │   │
│  │                    DATABASE LAYER (SQLite)                       │  │   │
│  │                                                                   │  │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │  │   │
│  │  │DBInteraction │  │DBPriceHistory│  │DBConnection  │          │  │   │
│  │  │              │  │              │  │              │          │  │   │
│  │  │ user_id      │  │ user_id      │  │ user_id      │          │  │   │
│  │  │ type         │  │ provider     │  │ provider     │          │  │   │
│  │  │ provider     │  │ ride_type    │  │ credentials  │          │  │   │
│  │  │ details      │  │ price        │  │ status       │          │  │   │
│  │  │ timestamp    │  │ locations    │  │              │          │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘          │  │   │
│  │                                                                   │  │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │  │   │
│  │  │DBOrder       │  │DBConversation│  │DBMessage     │          │  │   │
│  │  │              │  │              │  │              │          │  │   │
│  │  │ user_id      │  │ id           │  │ conversation │          │  │   │
│  │  │ partner      │  │ title        │  │ role         │          │  │   │
│  │  │ status       │  │ date         │  │ content      │          │  │   │
│  │  │ details      │  │              │  │              │          │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘          │  │   │
│  └───────────────────────────────────────────────────────────────────┘  │   │
└─────────────────────────────────────────────────────────────────────────┘   │
                                      │                                        │
                                      ▼                                        │
┌─────────────────────────────────────────────────────────────────────────────┐
│                        EXTERNAL APIs                                         │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ Uber API     │  │ Careem API   │  │ Bolt API     │  │ RTA API      │   │
│  │              │  │              │  │              │  │              │   │
│  │ /estimates   │  │ /estimates   │  │ /estimates   │  │ /routes      │   │
│  │ /requests    │  │ /booking     │  │ /booking     │  │ /schedules   │   │
│  │ /status      │  │ /status      │  │ /status      │  │ /stations    │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Examples

### Example 1: Price Comparison Request

```
1. User: "How much from Downtown to Marina?"
   │
   ▼
2. Frontend → POST /history/generate
   │
   ▼
3. GeminiService.generate_response()
   │
   ├─ Detects mobility intent
   ├─ Extracts locations (Downtown, Marina)
   │
   ▼
4. MobilityAggregator.compare_prices()
   │
   ├─ Calls UberService.get_price_estimates()
   ├─ Calls CareemService.get_price_estimates()
   └─ Calls BoltService.get_price_estimates()
   │
   ▼
5. Each service:
   ├─ Makes API call to provider
   ├─ Logs to DBInteraction (type: "price_check")
   └─ Logs to DBPriceHistory
   │
   ▼
6. MobilityAggregator.format_comparison()
   │
   ├─ Sorts by price
   └─ Returns formatted results
   │
   ▼
7. GeminiService formats AI response
   │
   ▼
8. Frontend displays: "Here are your options:
   - Careem GO: AED 35-40 (cheapest!)
   - Uber X: AED 38-45
   - Bolt Economy: AED 36-42"
```

### Example 2: Booking Flow

```
1. User: "Book the cheapest option"
   │
   ▼
2. Frontend → POST /mobility/book-ride
   │
   ▼
3. MobilityAggregator.book_cheapest_ride()
   │
   ├─ Finds cheapest from recent comparison
   ├─ Identifies provider (e.g., Careem)
   │
   ▼
4. CareemService.book_ride()
   │
   ├─ POST to Careem API /booking
   ├─ Logs to DBInteraction (type: "booking")
   └─ Creates DBOrder (status: "pending")
   │
   ▼
5. Returns booking confirmation
   │
   ▼
6. Frontend shows: "✅ Careem GO booked!
   Driver: Ahmed (4.9★)
   ETA: 5 minutes
   Ride ID: CRM-12345"
```

### Example 3: Ride Tracking

```
1. User: "Where's my ride?"
   │
   ▼
2. Frontend → GET /mobility/ride-status/careem/CRM-12345
   │
   ▼
3. CareemService.get_ride_status()
   │
   ├─ GET from Careem API /status
   └─ Updates DBOrder (status: "in_progress")
   │
   ▼
4. Returns real-time status
   │
   ▼
5. Frontend shows: "🚗 Your Careem is 2 mins away
   Driver: Ahmed in white Toyota Camry
   Plate: Dubai 12345
   [Live Map]"
```

## Key Architecture Benefits

### 1. **Separation of Concerns**
- Routes handle HTTP
- Services handle business logic
- Models handle data persistence
- Each provider isolated

### 2. **Reusability**
- `BaseMobilityService` enforces consistency
- Common methods (logging, formatting) shared
- Easy to add new providers

### 3. **Testability**
```python
# Mock a provider for testing
class MockCareemService(BaseMobilityService):
    async def get_price_estimates(self, ...):
        return {"prices": [{"estimate": "AED 35-40"}]}
```

### 4. **Scalability**
- Add providers without changing existing code
- Database tracks all interactions
- Analytics built on interaction logs

### 5. **AI Integration**
- Gemini detects intent automatically
- Natural language → API calls
- Context-aware recommendations

## File Organization

```
LFSD/
├── services/
│   ├── mobility/
│   │   ├── __init__.py
│   │   ├── base_mobility_service.py      # Abstract interface
│   │   ├── mobility_aggregator.py        # Unified API
│   │   ├── uber_service.py               # Uber integration
│   │   ├── careem_service.py             # Careem integration
│   │   ├── bolt_service.py               # Bolt integration
│   │   └── rta_service.py                # RTA integration
│   ├── gemini_service.py                 # AI chat (updated)
│   └── connection_service.py             # OAuth management
├── models.py                              # Database models
├── mobility_routes.py                     # API endpoints
├── config.py                              # API keys
└── docs/
    ├── MOBILITY_INTEGRATION_ARCHITECTURE.md
    ├── MOBILITY_IMPLEMENTATION_CHECKLIST.md
    └── MOBILITY_ARCHITECTURE_DIAGRAM.md  # This file
```

## Next: Start Implementation

See `MOBILITY_IMPLEMENTATION_CHECKLIST.md` for step-by-step tasks!
