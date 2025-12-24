"""
End-to-End Test for Mobility Integration

This script tests the complete mobility system:
1. API endpoints
2. All providers
3. Price comparison
4. Booking flow
"""

import asyncio
import httpx
import json

BASE_URL = "http://localhost:8003"

async def test_endpoints():
    print("🧪 End-to-End Mobility Integration Test\n")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        # Test 1: List Providers
        print("\n1. Testing /mobility/providers")
        try:
            response = await client.get(f"{BASE_URL}/mobility/providers")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success: {data}")
                providers = data.get('providers', [])
                print(f"   Found {len(providers)} providers: {providers}")
            else:
                print(f"   ❌ Failed: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 2: Compare Prices
        print("\n2. Testing /mobility/compare-prices")
        try:
            params = {
                "start_lat": 25.2048,
                "start_lng": 55.2708,
                "end_lat": 25.1972,
                "end_lng": 55.2744
            }
            response = await client.get(f"{BASE_URL}/mobility/compare-prices", params=params)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success!")
                if data.get('success'):
                    options = data['data']['options']
                    print(f"   Found {len(options)} ride options")
                    print(f"\n   Top 3 Options:")
                    for opt in options[:3]:
                        print(f"   - {opt['provider'].title()} {opt['ride_type']}: {opt['estimate']}")
                    
                    if data['data'].get('cheapest'):
                        cheapest = data['data']['cheapest']
                        print(f"\n   💰 Cheapest: {cheapest['provider'].title()} {cheapest['ride_type']} ({cheapest['estimate']})")
            else:
                print(f"   ❌ Failed: {response.status_code}")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 3: Get Cheapest Option
        print("\n3. Testing /mobility/cheapest")
        try:
            params = {
                "start_lat": 25.2048,
                "start_lng": 55.2708,
                "end_lat": 25.1972,
                "end_lng": 55.2744
            }
            response = await client.get(f"{BASE_URL}/mobility/cheapest", params=params)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success!")
                if data.get('success') and data.get('data'):
                    cheapest = data['data']
                    print(f"   Provider: {cheapest['provider'].title()}")
                    print(f"   Type: {cheapest['ride_type']}")
                    print(f"   Price: {cheapest['estimate']}")
            else:
                print(f"   ❌ Failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 4: Book a Ride (Mock)
        print("\n4. Testing /mobility/book-ride")
        try:
            payload = {
                "provider": "bolt",
                "ride_type": "Bolt",
                "start_location": {
                    "lat": 25.2048,
                    "lng": 55.2708,
                    "address": "Downtown Dubai"
                },
                "end_location": {
                    "lat": 25.1972,
                    "lng": 55.2744,
                    "address": "Dubai Marina"
                }
            }
            response = await client.post(f"{BASE_URL}/mobility/book-ride", json=payload)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success!")
                if data.get('success'):
                    booking = data['data']
                    print(f"   Ride ID: {booking.get('ride_id')}")
                    print(f"   Status: {booking.get('status')}")
                    if booking.get('driver'):
                        driver = booking['driver']
                        print(f"   Driver: {driver.get('name')} ({driver.get('rating')}★)")
            else:
                print(f"   ❌ Failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ End-to-End Test Complete!\n")

if __name__ == "__main__":
    asyncio.run(test_endpoints())
