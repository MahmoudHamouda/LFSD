"""
Test script for RTA integration.

This script tests the RTA service and aggregator integration.
"""

import asyncio
import sys
sys.path.append('.')

from services.mobility.mobility_aggregator import MobilityAggregator


async def test_rta_integration():
    """Test the RTA integration."""
    print("🚗 Testing RTA Integration (Public Transit)\n")
    print("=" * 60)
    
    # Initialize aggregator
    aggregator = MobilityAggregator()
    
    # Test 1: List available providers
    print("\n1. Available Providers:")
    print(f"   {list(aggregator.providers.keys())}")
    
    # Test 2: Compare prices (Dubai Downtown to Marina)
    print("\n2. Comparing Prices (Downtown to Marina):")
    comparison = await aggregator.compare_prices(
        user_id="test-user",
        start_lat=25.2048,
        start_lng=55.2708,
        end_lat=25.1972,
        end_lng=55.2744
    )
    
    print(f"   Found {len(comparison['options'])} options from {comparison['provider_count']} provider(s)")
    
    # List all options
    print("\n   All Options:")
    for opt in comparison['options']:
        provider = opt['provider'].title()
        ride_type = opt['ride_type']
        price = opt['estimate']
        # Highlight public transit
        if opt.get('type') == 'public_transit':
            print(f"   - 🚆 {provider} {ride_type}: {price} (Public Transit)")
        else:
            print(f"   - 🚗 {provider} {ride_type}: {price}")
    
    if comparison['cheapest']:
        cheapest = comparison['cheapest']
        print(f"\n   💰 Cheapest Option:")
        print(f"      Provider: {cheapest['provider'].title()}")
        print(f"      Type: {cheapest['ride_type']}")
        print(f"      Price: {cheapest['estimate']}")
    
    # Test 3: Test booking RTA (ticket generation)
    print("\n3. Testing RTA Booking (Ticket Generation - Mock):")
    booking = await aggregator.book_ride(
        user_id="test-user",
        provider="rta",
        ride_type="Dubai Metro (Red Line)",
        start_location={"lat": 25.2048, "lng": 55.2708, "address": "Downtown Dubai"},
        end_location={"lat": 25.1972, "lng": 55.2744, "address": "Dubai Marina"}
    )
    
    if booking.get("success"):
        print(f"   ✅ Ticket Generated successfully!")
        print(f"      Ticket ID: {booking.get('ride_id')}")
        print(f"      Status: {booking.get('status')}")
        if booking.get('details'):
            details = booking['details']
            print(f"      Type: {details.get('ticket_type')}")
            print(f"      Zones: {details.get('zones')}")
            print(f"      Valid: {details.get('valid_until')}")
    else:
        print(f"   ❌ Booking failed: {booking.get('error')}")
    
    print("\n" + "=" * 60)
    print("✅ RTA Integration Test Complete!\n")


if __name__ == "__main__":
    asyncio.run(test_rta_integration())
