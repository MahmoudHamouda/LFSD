"""
Test script for Google Maps Service
"""
import asyncio
import os
from services.productivity.google_maps_service import get_google_maps_service

async def test_google_maps():
    print("🗺️ Testing Google Maps Service...")
    
    maps_service = get_google_maps_service()
    
    # Check if API key is set
    if not maps_service.api_key:
        print("⚠️ No Google Maps API Key found. Using mock data.")
    else:
        print("✅ Google Maps API Key found.")
        
    # Test 1: Geocoding
    print("\n📍 Test 1: Geocoding 'Dubai Mall'")
    location = await maps_service.geocode("Dubai Mall")
    if location:
        print(f"   Success: {location}")
    else:
        print("   Failed to geocode.")
        
    # Test 2: Reverse Geocoding
    print("\n📍 Test 2: Reverse Geocoding (25.1972, 55.2744)")
    address = await maps_service.reverse_geocode(25.1972, 55.2744)
    if address:
        print(f"   Success: {address}")
    else:
        print("   Failed to reverse geocode.")
        
    # Test 3: Distance Matrix
    print("\n🚗 Test 3: Distance Matrix (Downtown -> Marina)")
    origins = ["25.2048,55.2708"]  # Downtown
    destinations = ["25.0805,55.1403"]  # Marina
    
    matrix = await maps_service.get_distance_matrix(origins, destinations)
    if matrix:
        print("   Success: Got distance matrix response")
        if "rows" in matrix:
            element = matrix["rows"][0]["elements"][0]
            print(f"   Distance: {element.get('distance', {}).get('text')}")
            print(f"   Duration: {element.get('duration', {}).get('text')}")
    else:
        print("   Failed to get distance matrix.")
        
    print("\n✅ Google Maps Service Test Complete")

if __name__ == "__main__":
    asyncio.run(test_google_maps())
