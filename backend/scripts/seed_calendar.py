"""
Seed Calendar Events for Time User
Creates today's schedule with realistic events
"""
import sys
import os
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.models import User, CalendarEvent

DATABASE_URL = "postgresql+psycopg2://postgres:LfsdSecure2024!@136.119.201.13:5432/lfsd"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def seed_calendar_events():
    print("=== SEEDING CALENDAR EVENTS ===")
    
    session = Session()
    try:
        # Get time and super users
        time_user = session.query(User).filter_by(email='time@helm.com').first()
        super_user = session.query(User).filter_by(email='super@helm.com').first()
        
        if not time_user:
            print("❌ time@helm.com not found")
            return
        
        # Clear existing events
        deleted_time = session.query(CalendarEvent).filter_by(user_id=time_user.id).delete()
        print(f"Cleared {deleted_time} existing events for time@helm.com")
        
        if super_user:
            deleted_super = session.query(CalendarEvent).filter_by(user_id=super_user.id).delete()
            print(f"Cleared {deleted_super} existing events for super@helm.com")
        
        session.commit()
        
        # Create events for today and next 7 days
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Template events for a typical week
        event_templates = [
            # Today
            {"title": "Morning Standup", "hour": 9, "duration": 30, "day_offset": 0},
            {"title": "Deep Work Session", "hour": 10, "duration": 120, "day_offset": 0},
            {"title": "Lunch Break", "hour": 12, "duration": 60, "day_offset": 0},
            {"title": "Team Meeting", "hour": 14, "duration": 60, "day_offset": 0},
            {"title": "Code Review", "hour": 15, "duration": 60, "day_offset": 0},
            {"title": "Gym", "hour": 18, "duration": 60, "day_offset": 0},
            
            # Tomorrow
            {"title": "Morning Standup", "hour": 9, "duration": 30, "day_offset": 1},
            {"title": "Client Call", "hour": 10, "duration": 60, "day_offset": 1},
            {"title": "Focus Time", "hour": 11, "duration": 120, "day_offset": 1},
            {"title": "Lunch", "hour": 13, "duration": 60, "day_offset": 1},
            {"title": "1:1 with Manager", "hour": 15, "duration": 30, "day_offset": 1},
            
            # Day 2
            {"title": "Morning Standup", "hour": 9, "duration": 30, "day_offset": 2},
            {"title": "Project Planning", "hour": 10, "duration": 90, "day_offset": 2},
            {"title": "Lunch", "hour": 12, "duration": 60, "day_offset": 2},
            {"title": "Development Sprint", "hour": 13, "duration": 180, "day_offset": 2},
            
            # Day 3
            {"title": "Morning Standup", "hour": 9, "duration": 30, "day_offset": 3},
            {"title": "Design Review", "hour": 10, "duration": 60, "day_offset": 3},
            {"title": "Deep Work", "hour": 11, "duration": 120, "day_offset": 3},
            {"title": "Lunch", "hour": 13, "duration": 60, "day_offset": 3},
            {"title": "Team Sync", "hour": 14, "duration": 60, "day_offset": 3},
        ]
        
        # Create events for time user
        for template in event_templates:
            event_date = today + timedelta(days=template["day_offset"])
            start_time = event_date + timedelta(hours=template["hour"])
            end_time = start_time + timedelta(minutes=template["duration"])
            
            event = CalendarEvent(
                user_id=time_user.id,
                title=template["title"],
                start_time=start_time,
                end_time=end_time,
                source="manual",
                event_type="meeting" if "meeting" in template["title"].lower() or "call" in template["title"].lower() else "work"
            )
            session.add(event)
        
        # Create events for super user if exists
        if super_user:
            for template in event_templates[:10]:  # Subset for super user
                event_date = today + timedelta(days=template["day_offset"])
                start_time = event_date + timedelta(hours=template["hour"])
                end_time = start_time + timedelta(minutes=template["duration"])
                
                event = CalendarEvent(
                    user_id=super_user.id,
                    title=template["title"],
                    start_time=start_time,
                    end_time=end_time,
                    source="manual",
                    event_type="meeting" if "meeting" in template["title"].lower() else "work"
                )
                session.add(event)
        
        session.commit()
        
        # Verify
        print("\n=== VERIFICATION ===")
        time_count = session.query(CalendarEvent).filter_by(user_id=time_user.id).count()
        print(f"time@helm.com: {time_count} events")
        
        # Count today's events
        tomorrow = today + timedelta(days=1)
        today_count = session.query(CalendarEvent).filter(
            CalendarEvent.user_id == time_user.id,
            CalendarEvent.start_time >= today,
            CalendarEvent.start_time < tomorrow
        ).count()
        print(f"Today's events: {today_count}")
        
        if super_user:
            super_count = session.query(CalendarEvent).filter_by(user_id=super_user.id).count()
            print(f"super@helm.com: {super_count} events")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    seed_calendar_events()
    print("\n✅ CALENDAR SEEDING COMPLETE")
