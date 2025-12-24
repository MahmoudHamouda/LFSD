"""
Test script to verify Uber sandbox integration.
"""
import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_uber_integration():
    """Test Uber API sandbox connectivity."""
    print("=" * 60)
    print("UBER SANDBOX INTEGRATION VERIFICATION")
    print("=" * 60)
    
    # Check credentials
    uber_server_token = os.getenv("UBER_SERVER_TOKEN")
    uber_client_id = os.getenv("UBER_CLIENT_ID")
    uber_client_secret = os.getenv("UBER_CLIENT_SECRET")
    
    print("\n1. Checking credentials...")
    print(f"   UBER_SERVER_TOKEN: {'✓ Set' if uber_server_token else '✗ Missing'}")
    print(f"   UBER_CLIENT_ID: {'✓ Set' if uber_client_id else '✗ Missing'}")
    print(f"   UBER_CLIENT_SECRET: {'✓ Set' if uber_client_secret else '✗ Missing'}")
    
    if not uber_server_token:
        print("\n✗ UBER_SERVER_TOKEN is required for testing")
        return False
    
    # Test API connectivity
    print("\n2. Testing API connectivity...")
    try:
        import httpx
        
        # Test price estimates endpoint (sandbox)
        url = "https://api.uber.com/v1.2/estimates/price"
        headers = {
            "Authorization": f"Token {uber_server_token}",
            "Accept-Language": "en_US",
            "Content-Type": "application/json"
        }
        
        # Dubai coordinates (Downtown to Marina)
        params = {
            "start_latitude": 25.2048,
            "start_longitude": 55.2708,
            "end_latitude": 25.0772,
            "end_longitude": 55.1309
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params, timeout=10.0)
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✓ API Response: {response.status_code}")
                print(f"   ✓ Products found: {len(data.get('prices', []))}")
                
                if data.get('prices'):
                    print("\n   Sample product:")
                    product = data['prices'][0]
                    print(f"   - Name: {product.get('localized_display_name')}")
                    print(f"   - Estimate: {product.get('estimate', 'N/A')}")
                    print(f"   - Duration: {product.get('duration', 'N/A')} seconds")
                
                return True
            else:
                print(f"   ✗ API Error: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"   ✗ Connection error: {str(e)}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_uber_integration())
    sys.exit(0 if result else 1)
