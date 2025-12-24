import pytest
import json
from unittest.mock import MagicMock, AsyncMock
from services.gemini_service import GeminiService

@pytest.mark.asyncio
async def test_gemini_json_mobility_recommendation():
    # Setup mock DB
    db = MagicMock()
    service = GeminiService(db)
    
    # Mock MobilityAggregator
    service.mobility_aggregator = MagicMock()
    service.mobility_aggregator.compare_prices = AsyncMock(return_value={
        "cheapest": {"provider": "careem", "ride_type": "hala", "estimate": "AED 25"},
        "options": [
            {"provider": "careem", "ride_type": "hala", "estimate": "AED 25", "eta": "8 mins"},
            {"provider": "uber", "ride_type": "uberx", "estimate": "AED 30", "eta": "5 mins"}
        ]
    })
    
    # Directly mock internal methods to avoid complex DB/LLM dependencies in this unit test
    service._load_viv_context = MagicMock(return_value={
        "profile": {},
        "viv_indexes": {"financial": 80, "health": 80, "time": 10},
        "life_goals": [],
        "preferences": {},
        "crisis_mode": True
    })
    
    service._extract_intent = AsyncMock(return_value={
        "intent": "mobility_options",
        "location": "Dubai Mall"
    })

    # Mock Gemini model response for the final synthesis if it reaches that
    service.model = MagicMock()
    service.model.generate_content_async = AsyncMock()
    
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "type": "mobility_options",
        "data": {
            "options": [
                {"provider": "uber", "type": "uberx", "recommended": True, "reasoning": "Faster for busy schedule"}
            ]
        }
    })
    service.model.generate_content_async.return_value = mock_response

    context = {
        "user_id": "test-user", 
        "location": {"lat": 25.2048, "lng": 55.2708},
        "indices": {"financial": 80, "schedule": 10, "energy": 80}
    }
    history = [{"role": "user", "content": "Check prices for a ride to Dubai Mall"}]
    
    # We also need to mock _route_intent or the handlers it calls
    # Actually, if intent is mobility_options, it should call _handle_mobility_request
    service._handle_mobility_request = AsyncMock(return_value={
        "type": "mobility_options",
        "data": {
            "options": [
                {"provider": "uber", "type": "uberx", "recommended": True, "reasoning": "Faster for busy schedule"}
            ]
        }
    })
    
    response = await service.generate_response(history, context)
    data = json.loads(response)
    
    assert data.get("type") == "mobility_options"
    assert data['data']['options'][0]['recommended'] is True
