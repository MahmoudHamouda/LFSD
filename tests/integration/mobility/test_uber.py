"""
Test script for Uber API integration
"""
import asyncio
import sys
sys.path.append('.')
sys.path.append('services')

from services.uber_service import get_uber_service

async def test_uber_api():
    print("Testing Uber API Integration...")
    print("=" * 50)
    
    uber_service = get_uber_service()
    
    # Test with Dubai coordinates
    print("\n📍 Testing price estimates for Dubai...")
    result = await uber_service.get_price_estimates(
        start_latitude=25.2048,
        start_longitude=55.2708,
        end_latitude=25.1972,
        end_longitude=55.2744
    )
    
    print("\nAPI Response:")
    print(f"Success: {result.get('success', False)}")
    print(f"Mock Data: {result.get('mock', True)}")
    if result.get('error'):
        print(f"Error: {result['error']}")
    
    print("\nFormatted Response:")
    print(uber_service.format_price_response(result))
    
    print("\n" + "=" * 50)
    print("Test complete!")

if __name__ == "__main__":
    asyncio.run(test_uber_api())
