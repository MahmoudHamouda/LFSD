"""
Test script to verify WhatsApp Cloud API integration.
"""
import os
import sys
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_whatsapp_integration():
    """Test WhatsApp API connectivity."""
    print("=" * 60)
    print("WHATSAPP CLOUD API INTEGRATION VERIFICATION")
    print("=" * 60)
    
    # Check credentials
    whatsapp_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
    whatsapp_phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    
    print("\n1. Checking credentials...")
    print(f"   WHATSAPP_ACCESS_TOKEN: {'✓ Set' if whatsapp_token else '✗ Missing'}")
    print(f"   WHATSAPP_PHONE_NUMBER_ID: {'✓ Set' if whatsapp_phone_id else '✗ Missing'}")
    
    if not whatsapp_token or not whatsapp_phone_id:
        print("\n✗ WhatsApp credentials are required for testing")
        return False
    
    # Test API connectivity
    print("\n2. Testing API connectivity...")
    try:
        from services.messaging.whatsapp_service import WhatsAppService
        
        whatsapp = WhatsAppService()
        
        # Test sending a template message (hello_world is pre-approved)
        print("\n3. Sending test template message...")
        test_number = "201114444231"  # From the user's example
        
        result = await whatsapp.send_template_message(
            to=test_number,
            template_name="hello_world",
            language_code="en_US"
        )
        
        print(f"   ✓ Message sent successfully")
        print(f"   ✓ Message ID: {result.get('messages', [{}])[0].get('id')}")
        print(f"   ✓ Response: {result}")
        
        return True
                
    except Exception as e:
        print(f"   ✗ Connection error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_whatsapp_integration())
    sys.exit(0 if result else 1)
