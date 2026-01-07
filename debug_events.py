import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text

DB_URL = "postgresql+psycopg2://postgres:LfsdSecure2024!@136.119.201.13:5432/lfsd"

def seed_events():
    print("--- SEEDING EVENTS (DEBUG) ---")
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            # 1. Get User
            res = conn.execute(text("SELECT id FROM users WHERE email='time@helm.com'")).fetchone()
            if not res:
                print("User time@helm.com not found.")
                return
            uid = res[0]
            print(f"User Found: {uid}")

            # 2. Insert Events
            events = [
                {"title": "Deep Work", "cat": "Focus", "is_meeting": False},
                {"title": "Team Sync", "cat": "Meeting", "is_meeting": True},
                {"title": "Client Call", "cat": "Meeting", "is_meeting": True},
                {"title": "Project Planning", "cat": "Focus", "is_meeting": False}
            ]
            
            for i, e in enumerate(events):
                start = datetime.utcnow() - timedelta(hours=i*2)
                end = start + timedelta(hours=1)
                
                sql = text("""
                    INSERT INTO calendar_events (id, user_id, title, start_time, end_time, is_meeting, location_context)
                    VALUES (:id, :uid, :title, :start, :end, :is_mtg, 'Office')
                """)
                try:
                    conn.execute(sql, {
                        "id": str(uuid.uuid4()), "uid": uid, "title": e['title'],
                        "start": start, "end": end, "is_mtg": e['is_meeting']
                    })
                    print(f"Inserted event: {e['title']}")
                except Exception as ex:
                    print(f"Failed {e['title']}: {ex}")
            
            conn.commit()
            print("Events Committed.")
            
            # 3. Verify
            count = conn.execute(text("SELECT count(*) FROM calendar_events WHERE user_id=:uid"), {"uid": uid}).scalar()
            print(f"Final Event Count: {count}")

    except Exception as e:
        print(f"Connection Error: {e}")

if __name__ == "__main__":
    seed_events()
