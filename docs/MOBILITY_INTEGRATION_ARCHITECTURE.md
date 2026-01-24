# Mobility Integration Architecture

## Implementation Status

> **Last Updated**: January 2026

This document describes both implemented and planned mobility integrations. Current implementation status:

| Provider | Status | Implementation Type | Notes |
|----------|--------|-------------------|-------|
| **Uber** | ✅ Implemented | Sandbox API | Fully functional with Uber Sandbox API for price estimates and booking |
| **Careem** | 🔄 Mock Only | Mock Service | Service structure exists, returns simulated data, production API not integrated |
| **Bolt** | 🔄 Mock Only | Mock Service | Service structure exists, returns simulated data, production API not integrated |
| **RTA** | 🔄 Mock Only | Mock Service | Service structure exists, returns simulated transit data, production API not integrated |
| **Aggregator** | ✅ Implemented | Unified Interface | `MobilityAggregator` provides unified API across all providers |
| **API Routes** | ✅ Implemented | REST Endpoints | `/mobility/*` endpoints functional for all providers |

### What Works Today
- ✅ Price comparison across all 4 providers (Uber real, others mock)
- ✅ Ride booking through unified API
- ✅ Interaction logging and price history tracking
- ✅ AI chat integration for mobility requests

### What's Planned
- ⏳ Production API integration for Careem
- ⏳ Production API integration for Bolt
- ⏳ Production API integration for RTA
- ⏳ OAuth flows for user-authenticated bookings

## Overview
This document outlines the architecture for integrating mobility partners (Careem, Uber, Bolt, RTA) into the LFSD platform. The architecture supports both real API integrations (like Uber Sandbox) and mock implementations that provide realistic responses for development without requiring production credentials.

## Architecture Principles

### 1. **Unified Service Layer Pattern**
- Each mobility provider gets its own service class (following `uber_service.py` pattern)
- All services implement a common interface for consistency
- Services handle API communication, data transformation, and error handling

### 2. **Database-First Tracking**
- All customer interactions are logged to the local SQLite database
- Existing models (`DBInteraction`, `DBPriceHistory`, `DBConnection`) are reused
- New models added only when necessary for provider-specific data

### 3. **Graceful Degradation**
- Mock data fallback when APIs are unavailable
- Clear error messaging to users
- Logging for debugging and monitoring

## Directory Structure

```
LFSD/
├── services/
│   ├── mobility/                    # NEW: Mobility services directory
│   │   ├── __init__.py
│   │   ├── base_mobility_service.py # Abstract base class
│   │   ├── uber_service.py          # MOVE: Existing Uber service
│   │   ├── careem_service.py        # NEW: Careem integration
│   │   ├── bolt_service.py          # NEW: Bolt integration
│   │   ├── rta_service.py           # NEW: RTA (public transport)
│   │   └── mobility_aggregator.py   # NEW: Unified interface
│   ├── gemini_service.py
│   └── ...
├── models.py                        # Existing models (already has what we need!)
├── mobility_routes.py               # NEW: API routes for mobility
└── config.py                        # Add mobility API keys
```

## Data Models (Already Exist!)

Your existing `models.py` already has everything we need:

### 1. **DBInteraction** (Line 76-86)
```python
# Tracks all user interactions with mobility services
- interaction_type: "price_check", "booking", "location_update"
- provider: "uber", "careem", "bolt", "rta"
- details: JSON with full context
- conversation_id: Links to chat context
```

### 2. **DBPriceHistory** (Line 103-115)
```python
# Tracks price estimates over time
- provider: "uber", "careem", "bolt"
- ride_type: "UberX", "Careem GO", etc.
- start_location, end_location: JSON coordinates
- price_estimate, currency
```

### 3. **DBConnection** (Line 89-100)
```python
# Stores user OAuth tokens for providers
- provider: "uber", "careem", "bolt"
- credentials: Encrypted tokens
- status: "connected", "disconnected"
```

### 4. **DBOrder** (Line 44-53)
```python
# Tracks completed bookings
- partner: "uber", "careem", "bolt"
- status: "pending", "completed", "cancelled"
- details: JSON with ride details
```

## Service Architecture

### Base Mobility Service (Abstract Interface)

```python
# services/mobility/base_mobility_service.py

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

class BaseMobilityService(ABC):
    """Abstract base class for all mobility providers."""
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider name (e.g., 'uber', 'careem')"""
        pass
    
    @abstractmethod
    async def get_price_estimates(
        self,
        start_lat: float,
        start_lng: float,
        end_lat: Optional[float] = None,
        end_lng: Optional[float] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get price estimates for rides."""
        pass
    
    @abstractmethod
    async def book_ride(
        self,
        user_id: str,
        ride_type: str,
        start_location: Dict[str, Any],
        end_location: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Book a ride."""
        pass
    
    @abstractmethod
    async def get_ride_status(
        self,
        user_id: str,
        ride_id: str
    ) -> Dict[str, Any]:
        """Get status of an active ride."""
        pass
    
    # Common helper methods (implemented in base class)
    def log_interaction(self, user_id: str, interaction_type: str, details: Dict):
        """Log interaction to database."""
        # Implementation from uber_service.py
        pass
    
    def log_price_history(self, user_id: str, prices: List[Dict], locations: Dict):
        """Log price history to database."""
        # Implementation from uber_service.py
        pass
    
    def format_price_response(self, prices: List[Dict]) -> str:
        """Format prices for user display."""
        # Common formatting logic
        pass
```

### Provider-Specific Services

#### 1. Careem Service
```python
# services/mobility/careem_service.py

class CareemService(BaseMobilityService):
    """Careem API integration."""
    
    BASE_URL = "https://api.careem.com/v1"
    
    @property
    def provider_name(self) -> str:
        return "careem"
    
    async def get_price_estimates(self, ...):
        # Careem-specific API calls
        # Returns standardized format
        pass
    
    async def book_ride(self, ...):
        # Careem booking logic
        pass
    
    async def get_ride_status(self, ...):
        # Careem ride tracking
        pass
    
    # Careem-specific methods
    async def get_careem_packages(self):
        """Get Careem subscription packages."""
        pass
```

#### 2. Bolt Service
```python
# services/mobility/bolt_service.py

class BoltService(BaseMobilityService):
    """Bolt API integration."""
    
    BASE_URL = "https://api.bolt.eu/v1"
    
    @property
    def provider_name(self) -> str:
        return "bolt"
    
    # Implement abstract methods...
```

#### 3. RTA Service (Public Transport)
```python
# services/mobility/rta_service.py

class RTAService(BaseMobilityService):
    """RTA Dubai public transport integration."""
    
    BASE_URL = "https://api.rta.ae/v1"
    
    @property
    def provider_name(self) -> str:
        return "rta"
    
    async def get_transit_routes(
        self,
        start_lat: float,
        start_lng: float,
        end_lat: float,
        end_lng: float
    ) -> Dict[str, Any]:
        """Get public transit routes."""
        pass
    
    async def get_metro_schedule(self, station: str) -> Dict[str, Any]:
        """Get metro schedules."""
        pass
    
    async def get_bus_schedule(self, route: str) -> Dict[str, Any]:
        """Get bus schedules."""
        pass
```

### Mobility Aggregator (Unified Interface)

```python
# services/mobility/mobility_aggregator.py

class MobilityAggregator:
    """Unified interface for all mobility providers."""
    
    def __init__(self):
        self.uber = UberService()
        self.careem = CareemService()
        self.bolt = BoltService()
        self.rta = RTAService()
        
        self.providers = {
            'uber': self.uber,
            'careem': self.careem,
            'bolt': self.bolt,
            'rta': self.rta
        }
    
    async def compare_prices(
        self,
        user_id: str,
        start_lat: float,
        start_lng: float,
        end_lat: float,
        end_lng: float,
        providers: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get price estimates from multiple providers.
        Returns aggregated, sorted results.
        """
        if providers is None:
            providers = ['uber', 'careem', 'bolt']
        
        results = {}
        for provider_name in providers:
            provider = self.providers.get(provider_name)
            if provider:
                try:
                    estimates = await provider.get_price_estimates(
                        start_lat, start_lng, end_lat, end_lng, user_id
                    )
                    results[provider_name] = estimates
                except Exception as e:
                    results[provider_name] = {"error": str(e)}
        
        # Log comparison interaction
        self._log_comparison(user_id, results)
        
        return self._format_comparison(results)
    
    async def book_cheapest_ride(
        self,
        user_id: str,
        start_location: Dict,
        end_location: Dict
    ) -> Dict[str, Any]:
        """
        Compare prices and book the cheapest option.
        """
        comparison = await self.compare_prices(
            user_id,
            start_location['lat'],
            start_location['lng'],
            end_location['lat'],
            end_location['lng']
        )
        
        # Find cheapest
        cheapest = self._find_cheapest(comparison)
        
        # Book with that provider
        provider = self.providers[cheapest['provider']]
        return await provider.book_ride(
            user_id,
            cheapest['ride_type'],
            start_location,
            end_location
        )
    
    def _format_comparison(self, results: Dict) -> Dict[str, Any]:
        """Format comparison results for display."""
        all_options = []
        
        for provider, data in results.items():
            if 'prices' in data:
                for price in data['prices']:
                    all_options.append({
                        'provider': provider,
                        'ride_type': price.get('localized_display_name'),
                        'estimate': price.get('estimate'),
                        'low_estimate': price.get('low_estimate'),
                        'high_estimate': price.get('high_estimate'),
                        'duration': price.get('duration'),
                        'distance': price.get('distance')
                    })
        
        # Sort by low_estimate
        all_options.sort(key=lambda x: x.get('low_estimate', float('inf')))
        
        return {
            'options': all_options,
            'cheapest': all_options[0] if all_options else None,
            'provider_count': len(results)
        }
```

## API Routes

```python
# mobility_routes.py

from fastapi import APIRouter, Depends, HTTPException
from services.mobility.mobility_aggregator import MobilityAggregator
from authentication import get_current_user

router = APIRouter(prefix="/mobility", tags=["Mobility"])

@router.get("/compare-prices")
async def compare_prices(
    start_lat: float,
    start_lng: float,
    end_lat: float,
    end_lng: float,
    providers: Optional[str] = None,  # Comma-separated
    current_user = Depends(get_current_user)
):
    """Compare prices across mobility providers."""
    aggregator = MobilityAggregator()
    
    provider_list = providers.split(',') if providers else None
    
    results = await aggregator.compare_prices(
        current_user['id'],
        start_lat,
        start_lng,
        end_lat,
        end_lng,
        provider_list
    )
    
    return results

@router.post("/book-ride")
async def book_ride(
    provider: str,
    ride_type: str,
    start_location: Dict,
    end_location: Dict,
    current_user = Depends(get_current_user)
):
    """Book a ride with specific provider."""
    aggregator = MobilityAggregator()
    
    if provider not in aggregator.providers:
        raise HTTPException(404, f"Provider {provider} not found")
    
    service = aggregator.providers[provider]
    result = await service.book_ride(
        current_user['id'],
        ride_type,
        start_location,
        end_location
    )
    
    return result

@router.get("/ride-status/{provider}/{ride_id}")
async def get_ride_status(
    provider: str,
    ride_id: str,
    current_user = Depends(get_current_user)
):
    """Get status of an active ride."""
    aggregator = MobilityAggregator()
    
    if provider not in aggregator.providers:
        raise HTTPException(404, f"Provider {provider} not found")
    
    service = aggregator.providers[provider]
    return await service.get_ride_status(current_user['id'], ride_id)
```

## Configuration Updates

```python
# config.py additions

class Settings(BaseSettings):
    # Existing settings...
    
    # Mobility API Keys
    UBER_SERVER_TOKEN: str = Field("", description="Uber Server Token")
    CAREEM_API_KEY: str = Field("", description="Careem API Key")
    CAREEM_API_SECRET: str = Field("", description="Careem API Secret")
    BOLT_API_KEY: str = Field("", description="Bolt API Key")
    RTA_API_KEY: str = Field("", description="RTA Dubai API Key")
```

## Gemini Integration (AI Chat)

Update `gemini_service.py` to use the mobility aggregator:

```python
# In gemini_service.py

from services.mobility.mobility_aggregator import MobilityAggregator

class GeminiService:
    def __init__(self, db: Session):
        # Existing init...
        self.mobility = MobilityAggregator()
    
    async def generate_response(self, history, context):
        # Detect mobility intent
        if self._is_mobility_request(history):
            return await self._handle_mobility_request(history, context)
        
        # Existing logic...
    
    async def _handle_mobility_request(self, history, context):
        """Handle mobility-related requests."""
        # Extract locations from conversation
        locations = self._extract_locations(history)
        
        if locations['start'] and locations['end']:
            # Get price comparison
            comparison = await self.mobility.compare_prices(
                context['user_id'],
                locations['start']['lat'],
                locations['start']['lng'],
                locations['end']['lat'],
                locations['end']['lng']
            )
            
            # Format response
            return self._format_mobility_response(comparison)
```

## Database Interaction Tracking

All interactions are automatically logged using existing models:

```python
# Example: When user asks for prices
interaction = DBInteraction(
    id=str(uuid.uuid4()),
    user_id=user_id,
    interaction_type="price_check",
    provider="careem",  # or "uber", "bolt"
    details=json.dumps({
        "start": {"lat": 25.2048, "lng": 55.2708, "address": "Downtown Dubai"},
        "end": {"lat": 25.1972, "lng": 55.2744, "address": "Dubai Marina"},
        "prices": [...],
        "timestamp": datetime.utcnow().isoformat()
    }),
    conversation_id=conversation_id
)

# Example: When user books a ride
order = DBOrder(
    id=str(uuid.uuid4()),
    user_id=user_id,
    partner="careem",
    status="pending",
    details=json.dumps({
        "ride_id": "careem_12345",
        "ride_type": "Careem GO",
        "pickup": {...},
        "dropoff": {...},
        "price": 45.00,
        "currency": "AED"
    })
)
```

## Analytics & Insights

Query examples for tracking customer behavior:

```python
# Most used provider
SELECT provider, COUNT(*) as usage_count
FROM interactions
WHERE interaction_type = 'booking'
GROUP BY provider
ORDER BY usage_count DESC;

# Price trends over time
SELECT provider, ride_type, AVG(price_estimate) as avg_price, DATE(timestamp) as date
FROM price_history
WHERE start_location LIKE '%Downtown%'
  AND end_location LIKE '%Marina%'
GROUP BY provider, ride_type, DATE(timestamp)
ORDER BY date DESC;

# User preferences
SELECT user_id, provider, COUNT(*) as bookings
FROM orders
WHERE status = 'completed'
GROUP BY user_id, provider;
```

## Implementation Phases

### Phase 1: Foundation ✅ COMPLETED
- [x] Create `services/mobility/` directory
- [x] Implement `base_mobility_service.py`
- [x] Move `uber_service.py` to new structure
- [x] Create `mobility_aggregator.py`
- [x] Add `mobility_routes.py`

### Phase 2: Careem Integration 🔄 PARTIALLY COMPLETE
- [x] Implement `careem_service.py` (Mock version)
- [ ] Add Careem production API credentials to config
- [x] Test price comparison (with mock data)
- [ ] Test booking flow (with production API)

### Phase 3: Bolt Integration 🔄 PARTIALLY COMPLETE
- [x] Implement `bolt_service.py` (Mock version)
- [ ] Add Bolt production API credentials
- [x] Test multi-provider comparison (with mock data)

### Phase 4: RTA Integration 🔄 PARTIALLY COMPLETE
- [x] Implement `rta_service.py` (Mock version)
- [ ] Add RTA production API access
- [ ] Integrate with Gemini for transit suggestions

### Phase 5: AI Enhancement ✅ COMPLETED
- [x] Update Gemini service to detect mobility intents
- [x] Add natural language location extraction
- [x] Implement smart recommendations

## Benefits of This Architecture

1. **Scalability**: Easy to add new providers (just extend `BaseMobilityService`)
2. **Maintainability**: Each provider isolated in its own service
3. **Testability**: Mock providers for testing
4. **Consistency**: All providers follow same interface
5. **Tracking**: Automatic logging of all interactions
6. **Flexibility**: Can mix and match providers per user preference
7. **Resilience**: Graceful degradation with mock data

## Next Steps

1. Review this architecture
2. Approve implementation phases
3. Obtain API credentials for Careem, Bolt, RTA
4. Begin Phase 1 implementation
