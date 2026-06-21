import sys
import os
import asyncio
import logging

# Setup Logging to file
logging.basicConfig(filename="test_mobility_debug.log", level=logging.DEBUG)

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.models import Base, User, MobilityTrip, VivLog
from services.gemini_service import GeminiService

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def verify_mobility():
    db = SessionLocal()
    try:
        user_id = "user-123"
        user = User(id=user_id, email="test@test.com", hashed_password="pw")
        db.add(user)
        db.commit()
        logging.info("User created.")

        service = GeminiService(db)

        # Mock Intent Extraction
        async def mock_extract(*args, **kwargs):
            return {
                "intent": "mobility_booking",
                "destination": "Dubai Mall",
                "provider": "uber",
                "ride_type": "uberx",
            }

        service._extract_intent = mock_extract

        # Mock Context Loading
        service._load_viv_context = lambda uid: {
            "viv_indexes": {"financial": 50},
            "life_goals": [],
            "crisis_mode": False,
        }

        # Mock Mobility Aggregator Book Ride
        async def mock_book_ride(*args, **kwargs):
            return {
                "success": True,
                "ride_id": "ride-123",
                "eta": "5 mins",
                "cost": 50.0,
                "driver": {"name": "Test Driver"},
            }

        service.mobility_aggregator.book_ride = mock_book_ride

        # Mock connection service to return 'uber' as connected
        # We need to mock the return value object structure
        class ConnectionMock:
            def __init__(self, provider, status):
                self.provider = provider
                self.status = status

        service.connection_service.get_connections = lambda uid: [
            ConnectionMock("uber", "connected")
        ]

        logging.info("Calling generate_response")
        history = [{"role": "user", "content": "book uber to dubai mall"}]
        loop = asyncio.get_event_loop()
        response = loop.run_until_complete(service.generate_response(history, {}))

        logging.info(f"Response: {response}")

        # Verify MobilityTrip
        trip = db.query(MobilityTrip).filter(MobilityTrip.user_id == user_id).first()
        if trip:
            logging.info(
                f"SUCCESS: Trip {trip.id} found. Provider: {trip.provider}, Cost: {trip.cost_amount}"
            )
            print("SUCCESS_TRIP")
            if trip.cost_amount == 50.0 and trip.provider == "uber":
                print("SUCCESS_DATA_MATCH")
            else:
                print("FAILURE_DATA_MATCH")
                print(f"Expected 50.0/uber, got {trip.cost_amount}/{trip.provider}")
        else:
            logging.error("FAILURE: No trip found.")
            print("FAILURE_TRIP")

        # Verify VivLog
        viv_log = (
            db.query(VivLog)
            .filter(VivLog.user_id == user_id)
            .order_by(VivLog.timestamp.desc())
            .first()
        )
        if viv_log:
            logging.info(
                f"SUCCESS: Log {viv_log.id} found. Intent: {viv_log.user_intent}"
            )
            if "mobility_booking_uber" in viv_log.user_intent:
                print("SUCCESS_LOG")
            else:
                print(f"FAILURE_LOG_INTENT: {viv_log.user_intent}")
        else:
            logging.error("FAILURE: No VivLog found.")
            print("FAILURE_LOG")

    except Exception as e:
        logging.error(f"Test Exception: {e}", exc_info=True)
        print(f"ERROR: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    verify_mobility()
