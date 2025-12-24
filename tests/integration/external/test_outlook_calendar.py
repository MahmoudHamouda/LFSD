"""
Test script for Outlook Calendar Service
"""
import asyncio
from datetime import datetime, timedelta
from services.productivity.outlook_calendar_service import get_outlook_calendar_service

async def test_outlook_calendar():
    print("📧 Testing Outlook Calendar Service...")
    
    calendar_service = get_outlook_calendar_service()
    
    # Check if credentials are set
    if not calendar_service.client_id:
        print("⚠️ No Microsoft Graph credentials found. Using mock data.")
    else:
        print("✅ Microsoft Graph credentials found.")
        
    user_id = "test_user"
    now = datetime.now()
    next_week = now + timedelta(days=7)
    
    # Test 1: List Events
    print("\n📋 Test 1: List Events (Next 7 Days)")
    events = await calendar_service.list_events(user_id, now, next_week)
    print(f"   Found {len(events)} events:")
    for event in events:
        start = event.get("start", {}).get("dateTime", "Unknown")
        print(f"   - {event.get('subject')} at {start}")
        
    # Test 2: Check Availability
    print("\n✅ Test 2: Check Availability")
    # Check a time we know is busy (based on mock data logic)
    tomorrow_3pm = (now + timedelta(days=1)).replace(hour=15, minute=0, second=0, microsecond=0)
    end_3pm = tomorrow_3pm + timedelta(hours=1)
    
    is_available = await calendar_service.check_availability(user_id, tomorrow_3pm, end_3pm)
    print(f"   Available tomorrow at 3pm? {'Yes' if is_available else 'No (Conflict found)'}")
    
    # Check a free time
    tomorrow_10am = (now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)
    end_10am = tomorrow_10am + timedelta(hours=1)
    
    is_available_free = await calendar_service.check_availability(user_id, tomorrow_10am, end_10am)
    print(f"   Available tomorrow at 10am? {'Yes' if is_available_free else 'No'}")
    
    # Test 3: Create Event
    print("\n➕ Test 3: Create Event")
    new_event = await calendar_service.create_event(
        user_id,
        "Sync with Marketing",
        tomorrow_10am,
        end_10am,
        description="Review campaign performance",
        location="Teams"
    )
    
    if new_event:
        print(f"   Success: Created event '{new_event.get('subject')}'")
        print(f"   ID: {new_event.get('id')}")
        print(f"   Link: {new_event.get('webLink')}")
    else:
        print("   Failed to create event.")
        
    print("\n✅ Outlook Calendar Service Test Complete")

if __name__ == "__main__":
    asyncio.run(test_outlook_calendar())
