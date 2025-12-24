# Mobility Integration - Quick Reference

## 🚀 Quick Start

### Test the System
```bash
# Test all providers
python test_mobility_integration.py

# Test AI integration
python test_ai_mobility.py
```

### Use the API
```bash
# Get all providers
curl http://localhost:8002/mobility/providers

# Compare prices
curl "http://localhost:8002/mobility/compare-prices?start_lat=25.2048&start_lng=55.2708&end_lat=25.1972&end_lng=55.2744"

# Get cheapest option
curl "http://localhost:8002/mobility/cheapest?start_lat=25.2048&start_lng=55.2708&end_lat=25.1972&end_lng=55.2744"
```

### Use the Chat Interface
Just type in natural language:
- "How much to Dubai Mall?"
- "Book the cheapest ride to Marina"
- "Show me bus options to the airport"

## 📁 Key Files

| File | Purpose |
|------|---------|
| `services/mobility/mobility_aggregator.py` | Main entry point for all mobility operations |
| `services/gemini_service.py` | AI intent detection and natural language processing |
| `mobility_routes.py` | FastAPI endpoints |
| `frontend/src/pages/chat/Chat.tsx` | Frontend chat with location capture |

## 🔧 Adding a New Provider

1. Create `services/mobility/your_provider_service.py`:
```python
from .base_mobility_service import BaseMobilityService

class YourProviderService(BaseMobilityService):
    @property
    def provider_name(self) -> str:
        return "your_provider"
    
    async def get_price_estimates(self, ...):
        # Implement price fetching
        pass
    
    async def book_ride(self, ...):
        # Implement booking
        pass
```

2. Update `services/mobility/mobility_aggregator.py`:
```python
from .your_provider_service import YourProviderService

class MobilityAggregator:
    def __init__(self):
        # ...
        self.your_provider = YourProviderService()
        self.providers = {
            # ...
            'your_provider': self.your_provider
        }
```

3. Add config to `config.py`:
```python
YOUR_PROVIDER_API_KEY: str = Field("", description="...")
```

4. Test it:
```python
python test_your_provider_integration.py
```

## 🎯 Common Use Cases

### Get Price Comparison
```python
from services.mobility.mobility_aggregator import MobilityAggregator

aggregator = MobilityAggregator()
results = await aggregator.compare_prices(
    user_id="user-123",
    start_lat=25.2048,
    start_lng=55.2708,
    end_lat=25.1972,
    end_lng=55.2744
)

print(f"Cheapest: {results['cheapest']}")
```

### Book a Ride
```python
booking = await aggregator.book_ride(
    user_id="user-123",
    provider="bolt",
    ride_type="Bolt",
    start_location={"lat": 25.2048, "lng": 55.2708},
    end_location={"lat": 25.1972, "lng": 55.2744}
)

print(f"Ride ID: {booking['ride_id']}")
```

### Use AI for Natural Language
```python
from services.gemini_service import GeminiService

service = GeminiService(db)
response = await service.generate_response(
    history=[{"role": "user", "content": "Book cheapest to Marina"}],
    context={"location": {"lat": 25.2048, "lng": 55.2708}}
)

print(response)  # AI-formatted booking confirmation
```

## 🐛 Troubleshooting

### "No providers available"
- Check that services are initialized in `MobilityAggregator.__init__`
- Verify API keys in `.env`

### "Location not found"
- Frontend: Check browser permissions for location access
- Backend: Verify `context.location` is being passed

### "Intent not detected"
- Check `GEMINI_API_KEY` is set
- Review logs in `debug_gemini.log`
- Ensure prompt is clear (e.g., "Book a ride to X" not just "X")

## 📊 Database Schema

All interactions are logged automatically:

**DBInteraction** - Every price check and booking
**DBPriceHistory** - Price trends over time
**DBOrder** - Completed bookings
**DBConnection** - Provider OAuth tokens

No migrations needed - uses existing models!

## 🔐 Security Notes

- API keys stored in `.env` (never commit!)
- Provider credentials encrypted in `DBConnection`
- User location only sent with explicit permission
- All API calls logged for audit

## 📈 Performance Tips

- Use `providers` parameter to limit comparison scope
- Cache geocoding results for common destinations
- Implement rate limiting for external APIs
- Use async/await for concurrent provider calls

---

**Need Help?** Check `docs/MOBILITY_INTEGRATION_COMPLETE.md` for full documentation.
