"""
Test script for AI Mobility Enhancement.

Tests the GeminiService's ability to:
1. Detect mobility intent
2. Use context location
3. Trigger aggregator
"""

import asyncio
import sys
import os
from unittest.mock import MagicMock

# Add project root to path
sys.path.append('.')

from services.gemini_service import GeminiService

async def test_ai_mobility():
    print("🤖 Testing AI Mobility Enhancement\n")
    print("=" * 60)
    
    # Mock DB session
    mock_db = MagicMock()
    
    # Initialize service
    service = GeminiService(mock_db)
    
    # Mock context with location (Downtown Dubai)
    context = {
        "location": {
            "lat": 25.2048,
            "lng": 55.2708
        },
        "user_id": "test-user-ai"
    }
    
    # Test 1: Price Check Intent
    print("\n1. Testing Price Check Intent:")
    query1 = "How much is a ride to Dubai Marina?"
    print(f"   User: {query1}")
    
    response1 = await service.generate_response(
        history=[{"role": "user", "content": query1}],
        context=context
    )
    print(f"   AI: {response1[:100]}...") # Print first 100 chars
    
    if "Cheapest" in response1 or "Options" in response1:
        print("   ✅ Price check intent detected and handled")
    else:
        print("   ❌ Failed to detect price check intent")

    # Test 2: Booking Intent
    print("\n2. Testing Booking Intent:")
    query2 = "Book the cheapest ride to Dubai Marina"
    print(f"   User: {query2}")
    
    response2 = await service.generate_response(
        history=[{"role": "user", "content": query2}],
        context=context
    )
    print(f"   AI: {response2}")
    
    if "Booking Confirmed" in response2:
        print("   ✅ Booking intent detected and handled")
    else:
        print("   ❌ Failed to detect booking intent")
        
    print("\n" + "=" * 60)
    print("✅ AI Mobility Test Complete!\n")

if __name__ == "__main__":
    asyncio.run(test_ai_mobility())
