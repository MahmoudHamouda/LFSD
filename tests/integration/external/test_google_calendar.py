"""
Test script for Google Calendar Service
"""
import asyncio
from datetime import datetime, timedelta
from services.productivity.google_calendar_service import get_google_calendar_service

async def test_google_calendar():
    print("📅 Testing Google Calendar Service...")
    
    calendar_service = get_google_calendar_service()
    
    # Check if credentials are set
    if not calendar_service.client_id:
        print("⚠️ No Google Calendar credentials found. Using mock data.")
    else:
        print("✅ Google Calendar credentials found.")
        
    user_id = "test_user"
    now = datetime.now()
    next_week = now + timedelta(days=7)
    
    # Test 1: List Events
    print("\n📋 Test 1: List Events (Next 7 Days)")
    events = await calendar_service.list_events(user_id, now, next_week)
    print(f"   Found {len(events)} events:")
    for event in events:
        start = event.get("start", {}).get("dateTime", "Unknown")
        print(f"   - {event.get('summary')} at {start}")
        
    # Test 2: Check Availability
    print("\n✅ Test 2: Check Availability")
    # Check a time we know is busy (based on mock data logic)
    tomorrow_10am = (now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
    end_10am = tomorrow_10am + timedelta(hours=1)
    
    is_available = await calendar_service.check_availability(user_id, tomorrow_10am, end_10am)
    print(f"   Available tomorrow at 10am? {'Yes' if is_available else 'No (Conflict found)'}")
    
    # Check a free time
    tomorrow_2pm = (now + timedelta(days=1)).replace(hour=14, minute=0, second=0, microsecond=0)
    end_2pm = tomorrow_2pm + timedelta(hours=1)
    
    is_available_free = await calendar_service.check_availability(user_id, tomorrow_2pm, end_2pm)
    print(f"   Available tomorrow at 2pm? {'Yes' if is_available_free else 'No'}")
    
    # Test 3: Create Event
    print("\n➕ Test 3: Create Event")
    new_event = await calendar_service.create_event(
        user_id,
        "Coffee with Sarah",
        tomorrow_2pm,
        end_2pm,
        description="Discuss marketing strategy",
        location="Starbucks JBR"
    )
    
    if new_event:
        print(f"   Success: Created event '{new_event.get('summary')}'")
        print(f"   ID: {new_event.get('id')}")
        print(f"   Link: {new_event.get('htmlLink')}")
    else:
        print("   Failed to create event.")
        
    print("\n✅ Google Calendar Service Test Complete")

if __name__ == "__main__":
    asyncio.run(test_google_calendar())
