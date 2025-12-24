"""
Test script for Skyscanner Service
"""
import asyncio
from datetime import datetime, timedelta
from services.travel_hospitality.skyscanner_service import get_skyscanner_service

async def test_skyscanner():
    print("✈️ Testing Skyscanner Service...")
    
    skyscanner_service = get_skyscanner_service()
    
    # Check if credentials are set
    if not skyscanner_service.api_key:
        print("⚠️ No Skyscanner/RapidAPI Key found. Using mock data.")
    else:
        print("✅ Skyscanner API Key found.")
        
    origin = "DXB"
    destination = "LHR"
    travel_date = datetime.now() + timedelta(days=14)
    
    # Test 1: Search Flights
    print(f"\n🔍 Test 1: Search Flights ({origin} -> {destination})")
    print(f"   Date: {travel_date.strftime('%Y-%m-%d')}")
    
    flights = await skyscanner_service.search_flights(origin, destination, travel_date)
    
    print(f"   Found {len(flights)} flight options:")
    print("-" * 50)
    
    for flight in flights:
        airline = flight.get("airline")
        flight_num = flight.get("flight_number")
        price = flight.get("price", {}).get("amount")
        currency = flight.get("price", {}).get("currency")
        stops = flight.get("stops")
        duration = flight.get("duration_mins") // 60
        
        stop_text = "Direct" if stops == 0 else f"{stops} Stop(s)"
        
        print(f"   🛫 {airline} ({flight_num}) - {stop_text}")
        print(f"      Price: {currency} {price}")
        print(f"      Duration: ~{duration} hours")
        print(f"      Link: {flight.get('booking_link')}")
        print("-" * 50)
        
    print("\n✅ Skyscanner Service Test Complete")

if __name__ == "__main__":
    asyncio.run(test_skyscanner())
