"""
Test script to verify Stripe sandbox integration.
"""
import os
import sys
import asyncio
from dotenv import load_dotenv
import stripe

# Load environment variables
load_dotenv()

async def test_stripe_integration():
    """Test Stripe API connectivity."""
    print("=" * 60)
    print("STRIPE SANDBOX INTEGRATION VERIFICATION")
    print("=" * 60)
    
    # Check credentials
    stripe_secret_key = os.getenv("STRIPE_SECRET_KEY")
    stripe_publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY")
    
    print("\n1. Checking credentials...")
    print(f"   STRIPE_SECRET_KEY: {'✓ Set' if stripe_secret_key else '✗ Missing'}")
    print(f"   STRIPE_PUBLISHABLE_KEY: {'✓ Set' if stripe_publishable_key else '✗ Missing'}")
    
    if not stripe_secret_key:
        print("\n✗ STRIPE_SECRET_KEY is required for testing")
        return False
        
    # Configure Stripe
    stripe.api_key = stripe_secret_key
    
    # Test API connectivity
    print("\n2. Testing API connectivity...")
    try:
        # List customers (simple read operation)
        customers = stripe.Customer.list(limit=1)
        print(f"   ✓ API Connection: Success")
        print(f"   ✓ Customers found: {len(customers)}")
        
        # Create a test payment intent
        print("\n3. Creating test PaymentIntent...")
        intent = stripe.PaymentIntent.create(
            amount=1000,  # $10.00
            currency='usd',
            payment_method_types=['card'],
            description='Integration Test Payment'
        )
        
        print(f"   ✓ PaymentIntent created: {intent.id}")
        print(f"   ✓ Status: {intent.status}")
        print(f"   ✓ Amount: {intent.amount} {intent.currency}")
        
        return True
                
    except stripe.error.AuthenticationError:
        print("   ✗ Authentication failed: Invalid API Key")
        return False
    except Exception as e:
        print(f"   ✗ Connection error: {str(e)}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_stripe_integration())
    sys.exit(0 if result else 1)
