import asyncio
import sys
import os
from typing import Dict, Any

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.gemini_service import GeminiService
from services.wealth_logic import validate_financial_goal
from services.time_utils import parse_time_slot
from models.database import SessionLocal

async def test_ambiguous_intent(service: GeminiService):
    print("\n--- Testing Ambiguous Intent ---")
    # Test 1: "How is my recovery?"
    history = []
    context = {}
    
    # We mock the _extract_intent to return what we expect from the LLM for this test
    # But ideally we want to test the actual LLM call if possible, or at least the routing logic.
    # Since we can't easily mock the LLM response without a mock library, we will test the _route_intent logic
    # by manually constructing the intent_data.
    
    intent_data = {
        "intent": "needs_clarification",
        "entities": {"question": "Do you mean physical recovery or financial debt recovery?"}
    }
    
    response = await service._route_intent(intent_data, context, "user-123")
    print(f"Input: 'How is my recovery?'")
    print(f"Response: {response}")
    
    assert response['type'] == 'text'
    assert "mean physical recovery" in response['text']
    print("PASS: Ambiguous intent handled correctly.")

async def test_financial_advisory(service: GeminiService):
    print("\n--- Testing Financial Advisory ---")
    # Test 2: "Can I afford a $500 watch?"
    intent_data = {
        "intent": "financial_advisory",
        "original_text": "Can I afford a $500 watch?",
        "entities": {"amount": 500, "item": "watch"}
    }
    context = {}
    
    response = await service._route_intent(intent_data, context, "user-123")
    print(f"Input: 'Can I afford a $500 watch?'")
    print(f"Response Type: {response['type']}")
    print(f"Response Text: {response['text']}")
    
    assert response['type'] == 'financial_advisory'
    # We can't assert the exact text as it comes from LLM, but it should be a string
    assert isinstance(response['text'], str)
    print("PASS: Financial advisory routed and executed.")

async def test_financial_goal_validation():
    print("\n--- Testing Financial Goal Validation ---")
    # Test 3: Unrealistic Goal
    context_data = {"monthly_income": 5000, "fixed_expenses": 2500}
    
    # Case A: Valid
    error = validate_financial_goal(1000, context_data)
    assert error is None
    print("PASS: Valid goal accepted.")
    
    # Case B: Invalid (Too high)
    error = validate_financial_goal(4000, context_data)
    print(f"Goal: 4000, Income: 5000, Fixed: 2500 -> Error: {error}")
    assert error is not None
    assert "Unrealistic Goal" in error
    print("PASS: Unrealistic goal rejected.")

async def test_time_parsing():
    print("\n--- Testing Time Parsing ---")
    # Test 4: "3 pm" -> Future 3 PM
    import datetime
    
    # Mock "now" is tricky without freezegun, but we can check if it's in the future
    dt = parse_time_slot("3 pm")
    print(f"Input: '3 pm' -> Parsed: {dt}")
    
    assert dt is not None
    # If run before 3pm, it might be today 3pm. If after, tomorrow 3pm.
    # But definitely should have time 15:00
    assert dt.hour == 15
    assert dt.minute == 0
    print("PASS: Time parsed correctly.")

async def main():
    db = SessionLocal()
    service = GeminiService(db)
    
    await test_ambiguous_intent(service)
    await test_financial_advisory(service)
    await test_financial_goal_validation()
    await test_time_parsing()
    
    print("\nALL TESTS PASSED")

if __name__ == "__main__":
    asyncio.run(main())
