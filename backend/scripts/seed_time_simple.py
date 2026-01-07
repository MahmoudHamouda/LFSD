"""
Simplified Calendar and Time Score Seeder
Creates calendar events and time scores without using time_service to avoid import issues
"""
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.models import User, CalendarEvent, TimeScore

DATABASE_URL = "postgresql+psycopg2://postgres:LfsdSecure2024!@136.119.201.13:5432/lfsd"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def seed_simple():
    print("=== SIMPLIFIED CALENDAR AND TIME SCORE SEEDING ===")
    
    session = Session()
    try:
        # Get time user
        time_user = session.query(User).filter_by(email='time@helm.com').first()
        
        if not time_user:
            print("❌ time@helm.com not found")
            return
        
        print(f"Processing {time_user.email}")
        
        # Clear existing data
        deleted_events = session.query(CalendarEvent).filter_by(user_id=time_user.id).delete()
        deleted_scores = session.query(TimeScore).filter_by(user_id=time_user.id).delete()
        print(f"Cleared {deleted_events} events and {deleted_scores} scores")
        session.commit()
        
        # Create calendar events for past 30 days
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        for day_offset in range(30):
            event_date = today - timedelta(days=day_offset)
            
            # Skip weekends
            if event_date.weekday() >= 5:
                continue
            
            # Morning standup
            session.add(CalendarEvent(
                user_id=time_user.id,
                title="Morning Standup",
                start_time=event_date + timedelta(hours=9),
                end_time=event_date + timedelta(hours=9, minutes=30),
                is_meeting=True,
                attendee_count=5
            ))
            
            # Deep work
            session.add(CalendarEvent(
                user_id=time_user.id,
                title="Deep Work",
                start_time=event_date + timedelta(hours=10),
                end_time=event_date + timedelta(hours=12),
                is_meeting=False,
                attendee_count=0
            ))
            
            # Lunch
            session.add(CalendarEvent(
                user_id=time_user.id,
                title="Lunch",
                start_time=event_date + timedelta(hours=12),
                end_time=event_date + timedelta(hours=13),
                is_meeting=False,
                attendee_count=0
            ))
            
            # Afternoon work
            if day_offset % 2 == 0:
                session.add(CalendarEvent(
                    user_id=time_user.id,
                    title="Team Meeting",
                    start_time=event_date + timedelta(hours=14),
                    end_time=event_date + timedelta(hours=15),
                    is_meeting=True,
                    attendee_count=8
                ))
            
            session.add(CalendarEvent(
                user_id=time_user.id,
                title="Focus Time",
                start_time=event_date + timedelta(hours=15, minutes=30),
                end_time=event_date + timedelta(hours=17),
                is_meeting=False,
                attendee_count=0
            ))
        
        session.commit()
        event_count = session.query(CalendarEvent).filter_by(user_id=time_user.id).count()
        print(f"✅ Created {event_count} calendar events")
        
        # Create TimeScore directly with reasonable values
        time_score = TimeScore(
            user_id=time_user.id,
            overall_score=72.0,
            schedule_coverage_score=85.0,
            planning_habit_score=75.0,
            focus_blocks_score=80.0,
            meeting_load_score=65.0,
            context_switching_score=70.0,
            weekly_rhythm_score=75.0,
            time_alignment_score=60.0,
            time_window="last_30_days",
            data_sources_json={"calendar": True},
            total_scheduled_hours=160.0,
            total_meeting_hours=40.0,
            total_focus_hours=80.0,
            avg_events_per_day=4.5
        )
        
        session.add(time_score)
        session.commit()
        print(f"✅ Time score created: {time_score.overall_score}")
        print(f"   - Schedule Coverage: {time_score.schedule_coverage_score}")
        print(f"   - Planning Habit: {time_score.planning_habit_score}")
        print(f"   - Focus Blocks: {time_score.focus_blocks_score}")
        
        print("\n=== VERIFICATION ===")
        events = session.query(CalendarEvent).filter_by(user_id=time_user.id).count()
        scores = session.query(TimeScore).filter_by(user_id=time_user.id).count()
        print(f"{time_user.email}: {events} events, {scores} time scores")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    seed_simple()
    print("\n✅ SEEDING COMPLETE")
