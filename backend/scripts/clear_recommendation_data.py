import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.models import User, RecurringBill, MobilityTrip, HealthDailySummary, VivIndex

# Hardcoded DB URL for dev environment (Consistent with config.py default)
DATABASE_URL = "sqlite:///lfsd_v2.db"

def clear_data():
    print("Connecting to database...")
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Target steward@helm.com and health@helm.com
        emails = ["steward@helm.com", "health@helm.com"]
        
        for email in emails:
            user = session.query(User).filter(User.email == email).first()
            if not user:
                print(f"User {email} not found. Skipping.")
                continue
                
            print(f"Clearing data for {email} ({user.id})...")
            
            # 1. Clear Bills (created by seed)
            deleted_bills = session.query(RecurringBill).filter(RecurringBill.user_id == user.id).delete()
            print(f"Deleted {deleted_bills} recurring bills.")
            
            # 2. Clear Mobility Trips (created by seed)
            deleted_trips = session.query(MobilityTrip).filter(MobilityTrip.user_id == user.id).delete()
            print(f"Deleted {deleted_trips} mobility trips.")
            
            # 3. Clear Health Summaries (created by seed)
            deleted_health = session.query(HealthDailySummary).filter(HealthDailySummary.user_id == user.id).delete()
            print(f"Deleted {deleted_health} health summaries.")
            
            # 4. Clear VivIndex? (Maybe keep it, but reset?)
            # treat_engine uses VivIndex. If we want to clear treats, we shouldn't delete index, 
            # but maybe scores will be low if we don't seed them?
            # Actually, seed_data didn't add VivIndex for steward logic (seeding.py does).
            # I won't delete VivIndex to avoid breaking Dashboard layout (which might expect it).
            
        session.commit()
        print("✅ Data cleared successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    clear_data()
