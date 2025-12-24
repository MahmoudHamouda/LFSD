"""
Test script for mobility integration.

This script tests the new mobility services without requiring app.py changes.
"""

import asyncio
import sys
sys.path.append('.')

from services.mobility.mobility_aggregator import MobilityAggregator


async def test_mobility_integration():
    """Test the mobility integration."""
    print("🚗 Testing Mobility Integration\n")
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
        start_lat=25.2048,  # Downtown Dubai
        start_lng=55.2708,
        end_lat=25.1972,    # Dubai Marina
        end_lng=55.2744
    )
    
    print(f"   Found {len(comparison['options'])} options from {comparison['provider_count']} provider(s)")
    
    if comparison['cheapest']:
        cheapest = comparison['cheapest']
        print(f"\n   💰 Cheapest Option:")
        print(f"      Provider: {cheapest['provider'].title()}")
        print(f"      Type: {cheapest['ride_type']}")
        print(f"      Price: {cheapest['estimate']}")
        print(f"      Duration: ~{cheapest['duration'] // 60} mins")
    
    # Test 3: Format for display
    print("\n3. Formatted Display:")
    formatted = aggregator.format_comparison_for_display(comparison)
    print(formatted)
    
    # Test 4: Test booking (mock)
    print("\n4. Testing Booking (Mock):")
    booking = await aggregator.book_ride(
        user_id="test-user",
        provider="uber",
        ride_type="UberX",
        start_location={"lat": 25.2048, "lng": 55.2708, "address": "Downtown Dubai"},
        end_location={"lat": 25.1972, "lng": 55.2744, "address": "Dubai Marina"}
    )
    
    if booking.get("success"):
        print(f"   ✅ Booking successful!")
        print(f"      Ride ID: {booking.get('ride_id')}")
        print(f"      Status: {booking.get('status')}")
        if booking.get('driver'):
            driver = booking['driver']
            print(f"      Driver: {driver.get('name')} ({driver.get('rating')}★)")
            print(f"      Vehicle: {driver.get('vehicle')}")
        print(f"      ETA: {booking.get('eta')} minutes")
        if booking.get('mock'):
            print(f"      ⚠️  This is a mock response (OAuth not implemented)")
    else:
        print(f"   ❌ Booking failed: {booking.get('error')}")
    
    print("\n" + "=" * 60)
    print("✅ Mobility Integration Test Complete!\n")


if __name__ == "__main__":
    asyncio.run(test_mobility_integration())
