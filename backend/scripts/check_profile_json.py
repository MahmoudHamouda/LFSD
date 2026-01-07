"""
Check time user's profile_json to see what conflicts with TimeScore
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

def check_profile_json():
    print("=== CHECKING TIME USER PROFILE_JSON ===")
    
    session = Session()
    try:
        time_user = session.query(User).filter_by(email='time@helm.com').first()
        
        if not time_user:
            print("❌ time@helm.com not found")
            return
        
        print(f"User ID: {time_user.id}")
        print(f"Email: {time_user.email}")
        
        if time_user.profile_json:
            print("\n=== PROFILE_JSON CONTENTS ===")
            print(json.dumps(time_user.profile_json, indent=2))
            
            if 'onboarding_breakdown' in time_user.profile_json:
                breakdown = time_user.profile_json['onboarding_breakdown']
                print("\n=== ONBOARDING_BREAKDOWN ===")
                
                if 'time' in breakdown:
                    print("\n⚠️  TIME BREAKDOWN EXISTS IN PROFILE_JSON:")
                    print(json.dumps(breakdown['time'], indent=2))
                    print("\n❌ This is why the TimeScore fallback isn't triggering!")
                    print("The scores API checks `if not breakdown.get('time')` but it already exists in profile_json")
                else:
                    print("✅ No time breakdown in profile_json")
                    
                if 'financial' in breakdown:
                    print("\n📊 FINANCIAL BREAKDOWN:")
                    print(json.dumps(breakdown['financial'], indent=2))
                    
                if 'health' in breakdown:
                    print("\n💪 HEALTH BREAKDOWN:")
                    print(json.dumps(breakdown['health'], indent=2))
        else:
            print("✅ profile_json is None/empty")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    check_profile_json()
    print("\n✅ CHECK COMPLETE")
