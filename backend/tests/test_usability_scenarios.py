import sys
import os
import asyncio
import json
import traceback
from datetime import datetime

# Add backend to sys.path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.models import Base, User, VivIndex, LifeGoal, Connection
from services.gemini_service import GeminiService

# Setup In-Memory DB to avoid all file issues
DB_URL = "sqlite:///:memory:"
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Schema
Base.metadata.create_all(bind=engine)

TEST_USER_ID = "test-persona-user"

def setup_test_user(db):
    """Resets the test user to a clean state."""
    user = db.query(User).filter(User.id == TEST_USER_ID).first()
    if not user:
        user = User(
            id=TEST_USER_ID,
            email="persona@test.com",
            hashed_password="hashed_secret",
            profile_json={"name": "Persona Test"},
            viv_preferences={"risk_tolerance": "medium"}
        )
        db.add(user)
    
    # Clear old indexes
    db.query(VivIndex).filter(VivIndex.user_id == TEST_USER_ID).delete()
    
    # Ensure a basic life goal exists
    db.query(LifeGoal).filter(LifeGoal.user_id == TEST_USER_ID).delete()
    db.add(LifeGoal(
        user_id=TEST_USER_ID,
        title="Emergency Fund",
        target_amount=10000,
        saved_amount=5000,
        priority="high"
    ))
    
    db.commit()
    return user

def set_viv_index(db, financial, health, time):
    """Sets the user's current 'state'."""
    index = VivIndex(
        user_id=TEST_USER_ID,
        financial_score=financial,
        health_score=health,
        time_score=time,
        timestamp=datetime.utcnow()
    )
    db.add(index)
    db.commit()

async def run_simulation():
    db = SessionLocal()
    try:
        setup_test_user(db)
        service = GeminiService(db)
        
        scenarios = [
            {
                "name": "Steward Mode (Balanced/High)",
                "indices": {"financial": 80, "health": 80, "time": 80},
                "intent_data": {
                    "intent": "mobility_price_check",
                    "destination": "Dubai Mall",
                    "start_location": "Home"
                },
                "expected": "Balanced recommendation"
            },
            {
                "name": "Operator Mode (Fatigue/Low Health)",
                "indices": {"financial": 60, "health": 20, "time": 60},
                "intent_data": {
                    "intent": "mobility_price_check",
                    "destination": "Dubai Mall",
                    "start_location": "Home"
                },
                # We expect the system to pick Comfort/Ease over Price if Health is low
                "expected": "Prioritize comfort/energy conservation"
            },
            {
                "name": "Commander Mode (Urgency/Low Time)",
                "indices": {"financial": 60, "health": 60, "time": 10},
                "intent_data": {
                    "intent": "mobility_price_check",
                    "destination": "Airport",
                    "start_location": "Office"
                },
                # We expect the system to pick Speed over Price if Time is low
                "expected": "Prioritize speed/time"
            }
        ]

        print(f"\n{'='*60}")
        print(f"RUNNING USABILITY & HUMAN FACTORS SIMULATION")
        print(f"{'='*60}\n")

        # Mock Connection Service or ensure we have 'mock' providers
        # The gemini_service checks for connected providers.
        # We might need to mock get_connections or inject a connection for the test user.
        # Injecting a connection:
        db.query(Connection).filter(Connection.user_id == TEST_USER_ID).delete()
        db.add(Connection(user_id=TEST_USER_ID, provider="uber", status="connected"))
        db.commit()

        for sc in scenarios:
            print(f"--- SCENARIO: {sc['name']} ---")
            # 1. Set State
            ind = sc['indices']
            set_viv_index(db, ind['financial'], ind['health'], ind['time'])
            print(f"State Set: Financial={ind['financial']}, Health={ind['health']}, Time={ind['time']}")

            # 2. Prepare Context (Mimic what _load_viv_context does, but we let the service load it from DB to be real)
            context = service._load_viv_context(TEST_USER_ID)
            
            # 3. Simulate Request directly via _handle_mobility_request logic
            # We bypass _extract_intent to focus on the ADAPTATION logic in the handler
            intent_data = sc['intent_data']
            
            # Note: The service uses `mobility_aggregator`. We trust the mock data in it (it seemed hardcoded in previous files or calls API).
            # The `GeminiService.get_ride_estimates` had backward compat hardcoded, but `_handle_mobility_request` uses `mobility_aggregator`.
            # We hope `mobility_aggregator` works without external API keys or fails gracefully.
            # If it fails, we catch it.
            
            try:
                response = await service._route_intent(intent_data, context, TEST_USER_ID)
                
                if response and response.get('type') == 'mobility_options':
                    data = response.get('data', {})
                    options = data.get('options', [])
                    rec = next((o for o in options if o.get('recommended')), None)
                    
                    print(f"AI Tone/Response: {response.get('text')}")
                    if rec:
                        print(f"RECOMMENDATION: {rec['provider']} {rec['type']} - {rec['reasoning']}")
                    else:
                        print("RECOMMENDATION: None found.")
                    
                    print(f"Goal Impact Analysis: {data.get('goal_impact_analysis')}")
                else:
                    print(f"Response: {response}")

            except Exception as e:
                print(f"EXECUTION FAILED: {e}")
                traceback.print_exc()
            
            print("\n")

    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_simulation())
