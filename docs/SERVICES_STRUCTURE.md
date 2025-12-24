# Services Directory Structure

This document describes the organization of the `services/` directory, which follows the architecture outlined in `MULTI_SERVICE_INTEGRATION_PLAN.md`.

## Current Structure

```
services/
├── mobility/                    # Mobility & Transportation
│   ├── base_mobility_service.py
│   ├── mobility_aggregator.py
│   ├── uber_service.py
│   ├── careem_service.py
│   ├── bolt_service.py
│   └── rta_service.py
│
├── productivity/                # Calendar & Maps Services
│   ├── __init__.py
│   ├── base_calendar_service.py
│   ├── google_calendar_service.py
│   ├── google_maps_service.py
│   └── outlook_calendar_service.py
│
├── travel_hospitality/          # Travel & Accommodation
│   ├── __init__.py
│   └── skyscanner_service.py
│
├── financial_service/           # Financial Services
├── activity_feed_service/       # Activity Feeds
├── audit_log_service/           # Audit Logging
├── chat_service/                # Chat Management
├── notification_service/        # Notifications
├── partner_service/             # Partner Management
├── recommendation_service/      # Recommendations
├── user_management_service/     # User Management
├── gemini_service.py            # Gemini AI Integration
└── claude_service.py            # Claude AI Integration
```

## Service Categories

### 1. Mobility (`services/mobility/`)
**Purpose**: Ride-hailing and public transit integration.

**Providers**:
- Uber (Sandbox API)
- Careem (Mock)
- Bolt (Mock)
- RTA Dubai (Mock)

**Key Features**:
- Price comparison across providers
- Ride booking
- ETA calculation
- Provider aggregation

### 2. Productivity (`services/productivity/`)
**Purpose**: Calendar management and location services.

**Services**:
- **Google Calendar**: Event management, availability checking
- **Outlook Calendar**: Microsoft Graph integration
- **Google Maps**: Geocoding, distance matrix, directions

**Key Features**:
- Schedule management
- Location resolution
- Travel time calculation
- Cross-calendar support

### 3. Travel & Hospitality (`services/travel_hospitality/`)
**Purpose**: Flight and hotel booking.

**Services**:
- **Skyscanner**: Flight search and price comparison (via RapidAPI)
- **Booking.com**: Hotel search (planned)

**Key Features**:
- Flight search
- Price comparison
- Multi-stop routing
- Hotel availability

## Import Patterns

### Mobility Services
```python
from services.mobility.mobility_aggregator import get_mobility_aggregator
from services.mobility.uber_service import UberService
```

### Productivity Services
```python
from services.productivity.google_calendar_service import get_google_calendar_service
from services.productivity.google_maps_service import get_google_maps_service
from services.productivity.outlook_calendar_service import get_outlook_calendar_service
```

### Travel Services
```python
from services.travel_hospitality.skyscanner_service import get_skyscanner_service
```

## Test Scripts

Each service category has corresponding test scripts:

- `test_mobility_integration.py` - Mobility services
- `test_google_maps.py` - Google Maps
- `test_google_calendar.py` - Google Calendar
- `test_outlook_calendar.py` - Outlook Calendar
- `test_skyscanner.py` - Skyscanner

## Future Additions

### Planned Services (from MULTI_SERVICE_INTEGRATION_PLAN.md)

#### Food & Grocery (`services/food_grocery/`)
- Deliveroo
- Talabat
- InstaShop
- Noon Minutes

#### Lifestyle & Wellness (`services/lifestyle_wellness/`)
- ClassPass
- Fresha
- PlatinumList
- Dubai Calendar

#### Financial (`services/financial/`)
- Tarabut Gateway
- Lean Technologies

## Configuration

All service credentials are managed via `config.py` and `.env`:

```env
# Mobility
UBER_SERVER_TOKEN=
CAREEM_API_KEY=
BOLT_API_KEY=
RTA_API_KEY=

# Productivity
GOOGLE_MAPS_API_KEY=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
MICROSOFT_CLIENT_ID=
MICROSOFT_CLIENT_SECRET=

# Travel
RAPIDAPI_KEY=
SKYSCANNER_API_KEY=
BOOKING_API_KEY=
```

## Design Principles

1. **Separation of Concerns**: Each service category has its own directory
2. **Base Classes**: Abstract base classes define common interfaces
3. **Singleton Pattern**: Services use singleton pattern for efficiency
4. **Mock Support**: All services gracefully fall back to mock data when credentials are missing
5. **Aggregation**: Aggregator classes provide unified APIs across multiple providers
