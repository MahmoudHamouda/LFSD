"""
Seed Calendar Events and Calculate Time Scores
Creates realistic calendar events and calculates time scores for time and super users
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

# Import time_service after models are loaded
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services'))
from time_service import calculate_time_score

def seed_calendar_and_scores():
    print("=== SEEDING CALENDAR EVENTS AND TIME SCORES ===")
    
    session = Session()
    try:
        # Get time and super users
        time_user = session.query(User).filter_by(email='time@helm.com').first()
        super_user = session.query(User).filter_by(email='super@helm.com').first()
        
        if not time_user:
            print("❌ time@helm.com not found")
            return
        
        users_to_seed = [time_user]
        if super_user:
            users_to_seed.append(super_user)
        
        for user in users_to_seed:
            print(f"\n--- Processing {user.email} ---")
            
            # Clear existing calendar events and time scores
            deleted_events = session.query(CalendarEvent).filter_by(user_id=user.id).delete()
            deleted_scores = session.query(TimeScore).filter_by(user_id=user.id).delete()
            print(f"Cleared {deleted_events} events and {deleted_scores} time scores")
            session.commit()
            
            # Create calendar events for the past 30 days
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            
            for day_offset in range(30):
                event_date = today - timedelta(days=day_offset)
                
                # Skip weekends for work events
                if event_date.weekday() >= 5:
                    continue
                
                # Morning standup (9:00 AM, 30 min)
                session.add(CalendarEvent(
                    user_id=user.id,
                    title="Morning Standup",
                    start_time=event_date + timedelta(hours=9),
                    end_time=event_date + timedelta(hours=9, minutes=30),
                    is_meeting=True,
                    attendee_count=5
                ))
                
                # Deep work session (10:00 AM, 2 hours)
                session.add(CalendarEvent(
                    user_id=user.id,
                    title="Deep Work Session",
                    start_time=event_date + timedelta(hours=10),
                    end_time=event_date + timedelta(hours=12),
                    is_meeting=False,
                    attendee_count=0
                ))
                
                # Lunch break (12:00 PM, 1 hour)
                session.add(CalendarEvent(
                    user_id=user.id,
                    title="Lunch Break",
                    start_time=event_date + timedelta(hours=12),
                    end_time=event_date + timedelta(hours=13),
                    is_meeting=False,
                    attendee_count=0
                ))
                
                # Afternoon meetings (vary by day)
                if day_offset % 3 == 0:
                    # Team meeting
                    session.add(CalendarEvent(
                        user_id=user.id,
                        title="Team Meeting",
                        start_time=event_date + timedelta(hours=14),
                        end_time=event_date + timedelta(hours=15),
                        is_meeting=True,
                        attendee_count=8
                    ))
                elif day_offset % 3 == 1:
                    # 1:1 with manager
                    session.add(CalendarEvent(
                        user_id=user.id,
                        title="1:1 with Manager",
                        start_time=event_date + timedelta(hours=15),
                        end_time=event_date + timedelta(hours=15, minutes=30),
                        is_meeting=True,
                        attendee_count=2
                    ))
                
                # Focus time (varies)
                if day_offset % 2 == 0:
                    session.add(CalendarEvent(
                        user_id=user.id,
                        title="Focus Time",
                        start_time=event_date + timedelta(hours=15, minutes=30),
                        end_time=event_date + timedelta(hours=17),
                        is_meeting=False,
                        attendee_count=0
                    ))
            
            session.commit()
            
            # Count created events
            event_count = session.query(CalendarEvent).filter_by(user_id=user.id).count()
            print(f"✅ Created {event_count} calendar events")
            
            # Calculate time score
            print("Calculating time score...")
            time_score = calculate_time_score(session, user.id, window="month")
            
            if time_score:
                session.add(time_score)
                session.commit()
                print(f"✅ Time score calculated: {time_score.overall_score}")
                print(f"   - Schedule Coverage: {time_score.schedule_coverage_score}")
                print(f"   - Planning Habit: {time_score.planning_habit_score}")
                print(f"   - Focus Blocks: {time_score.focus_blocks_score}")
                print(f"   - Meeting Load: {time_score.meeting_load_score}")
                print(f"   - Context Switching: {time_score.context_switching_score}")
                print(f"   - Weekly Rhythm: {time_score.weekly_rhythm_score}")
                print(f"   - Time Alignment: {time_score.time_alignment_score}")
            else:
                print("⚠️  Could not calculate time score (no events)")
        
        print("\n=== VERIFICATION ===")
        for user in users_to_seed:
            events = session.query(CalendarEvent).filter_by(user_id=user.id).count()
            scores = session.query(TimeScore).filter_by(user_id=user.id).count()
            print(f"{user.email}: {events} events, {scores} time scores")
        
    except Exception as e:
        session.rollback()
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    seed_calendar_and_scores()
    print("\n✅ SEEDING COMPLETE")
