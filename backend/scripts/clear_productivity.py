"""
Clear old productivity breakdown from time user's profile_json
This will force the API to use TimeScore table instead
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.models import User
import json

DATABASE_URL = "postgresql+psycopg2://postgres:LfsdSecure2024!@136.119.201.13:5432/lfsd"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def clear_productivity_breakdown():
    print("=== CLEARING OLD PRODUCTIVITY BREAKDOWN ===")
    
    session = Session()
    try:
        time_user = session.query(User).filter_by(email='time@helm.com').first()
        
        if not time_user:
            print("❌ time@helm.com not found")
            return
        
        if time_user.profile_json and 'onboarding_breakdown' in time_user.profile_json:
            breakdown = time_user.profile_json['onboarding_breakdown']
            
            if 'productivity' in breakdown:
                print("Found old productivity breakdown:")
                print(json.dumps(breakdown['productivity'], indent=2))
                
                # Remove productivity breakdown
                del breakdown['productivity']
                
                # Update user
                time_user.profile_json['onboarding_breakdown'] = breakdown
                session.commit()
                
                print("\n✅ Removed old productivity breakdown")
                print("TimeScore fallback will now trigger!")
            else:
                print("✅ No productivity breakdown found")
        else:
            print("✅ No profile_json or onboarding_breakdown")
        
    except Exception as e:
        session.rollback()
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    clear_productivity_breakdown()
    print("\n✅ COMPLETE")
