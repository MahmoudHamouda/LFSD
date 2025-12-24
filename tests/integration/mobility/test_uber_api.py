"""
Test Uber API call directly
"""
import asyncio
import sys
sys.path.append('.')

async def test():
    from services.uber_service import get_uber_service
    
    print("Testing Uber API...")
    uber = get_uber_service()
    print(f"Token configured: {bool(uber.server_token)}")
    print(f"Token: {uber.server_token[:20]}..." if uber.server_token else "No token")
    
    result = await uber.get_price_estimates(
        start_latitude=25.2048,
        start_longitude=55.2708,
        end_latitude=25.1972,
        end_longitude=55.2744
    )
    
    print("\nResult:")
    print(f"Mock: {result.get('mock', 'N/A')}")
    print(f"Error: {result.get('error', 'None')}")
    print(f"Prices count: {len(result.get('prices', []))}")
    
    if result.get('prices'):
        print("\nFirst price:")
        print(result['prices'][0])

asyncio.run(test())
