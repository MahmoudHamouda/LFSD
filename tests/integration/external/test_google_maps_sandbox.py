"""
Test script to verify Google Maps API integration.
"""
import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_google_maps_integration():
    """Test Google Maps API connectivity."""
    print("=" * 60)
    print("GOOGLE MAPS API INTEGRATION VERIFICATION")
    print("=" * 60)
    
    # Check credentials
    google_maps_key = os.getenv("GOOGLE_MAPS_API_KEY")
    google_client_id = os.getenv("GOOGLE_CLIENT_ID")
    google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    
    print("\n1. Checking credentials...")
    print(f"   GOOGLE_MAPS_API_KEY: {'✓ Set' if google_maps_key else '✗ Missing'}")
    print(f"   GOOGLE_CLIENT_ID: {'✓ Set' if google_client_id else '✗ Missing'}")
    print(f"   GOOGLE_CLIENT_SECRET: {'✓ Set' if google_client_secret else '✗ Missing'}")
    
    if not google_maps_key:
        print("\n✗ GOOGLE_MAPS_API_KEY is required for testing")
        return False
    
    # Test API connectivity
    print("\n2. Testing Google Maps API...")
    try:
        import httpx
        
        # Test Geocoding API
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "address": "Burj Khalifa, Dubai",
            "key": google_maps_key
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params, timeout=10.0)
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status')
                
                if status == 'OK':
                    print(f"   ✓ Geocoding API: Working")
                    results = data.get('results', [])
                    if results:
                        location = results[0]['geometry']['location']
                        print(f"   ✓ Location found: {location['lat']}, {location['lng']}")
                    
                    # Test Distance Matrix API
                    print("\n3. Testing Distance Matrix API...")
                    dm_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
                    dm_params = {
                        "origins": "25.2048,55.2708",  # Downtown Dubai
                        "destinations": "25.0772,55.1309",  # Dubai Marina
                        "key": google_maps_key
                    }
                    
                    dm_response = await client.get(dm_url, params=dm_params, timeout=10.0)
                    if dm_response.status_code == 200:
                        dm_data = dm_response.json()
                        if dm_data.get('status') == 'OK':
                            print(f"   ✓ Distance Matrix API: Working")
                            rows = dm_data.get('rows', [])
                            if rows and rows[0].get('elements'):
                                element = rows[0]['elements'][0]
                                if element.get('status') == 'OK':
                                    distance = element.get('distance', {}).get('text')
                                    duration = element.get('duration', {}).get('text')
                                    print(f"   ✓ Distance: {distance}")
                                    print(f"   ✓ Duration: {duration}")
                    
                    return True
                else:
                    print(f"   ✗ API Error: {status}")
                    print(f"   Message: {data.get('error_message', 'Unknown error')}")
                    return False
            else:
                print(f"   ✗ HTTP Error: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"   ✗ Connection error: {str(e)}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_google_maps_integration())
    sys.exit(0 if result else 1)
