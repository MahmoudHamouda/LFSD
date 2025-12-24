import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.database import Base, get_db
from models.models import User, VivIndex
from core.authentication import get_current_user
from app import create_app
import uuid

app = create_app()

# Setup DB
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_profile_update.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Create a test user instance
test_user_id = str(uuid.uuid4())
test_user = User(
    id=test_user_id,
    email="testprofile@example.com",
    hashed_password="fakehash",
    profile_json={"name": "Test User"},
    viv_preferences={}
)

from fastapi import Depends
from sqlalchemy.orm import Session

def override_get_current_user_with_db(db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == test_user_id).first()
    if not user:
        # Create if missing (lazy setup)
        user = User(
            id=test_user_id,
            email="testprofile@example.com",
            hashed_password="fakehash",
            profile_json={"name": "Test User"},
            viv_preferences={}
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user_with_db

client = TestClient(app)

def setup_module(module):
    # Initialize DB with user
    db = TestingSessionLocal()
    db.add(test_user)
    db.commit()
    db.close()

def test_update_profile_identity():
    payload = {
        "identity": {
            "firstName": "Updated",
            "lastName": "Name"
        }
    }
    response = client.patch("/api/user/me", json=payload)
    if response.status_code != 200:
        print(f"Update Identity Failed: {response.text}")
    assert response.status_code == 200
    data = response.json()
    print(f"DEBUG RESPONSE: {data}")
    assert data["user"]["identity"]["firstName"] == "Updated"
    assert data["user"]["identity"]["lastName"] == "Name"
    assert data["user"]["profile"]["name"] == "Updated Name"

def test_update_profile_onboarding_and_scores():
    # Update financial data
    payload = {
        "onboarding_data": {
            "monthly_income": 8000,
            "monthly_expenses": 3000,
            "has_debt": "no",
            "monthly_savings": 2000,
            
            # Health
            "sleep_hours": "7-8",
            "activity_level": "Active",
            
            # Productivity
            "work_hours_per_week": "40"
        }
    }
    response = client.patch("/api/user/me", json=payload)
    if response.status_code != 200:
        print(f"Update Onboarding Failed: {response.text}")
    assert response.status_code == 200
    data = response.json()
    
    # Verify Data update
    assert data["user"]["profile"]["onboarding_data"]["monthly_income"] == 8000
    
    # Verify Score Recalculation (Scores should be present in VivIndex)
    # The endpoint creates a new VivIndex entry
    db = TestingSessionLocal()
    viv_index = db.query(VivIndex).filter(VivIndex.user_id == test_user_id).order_by(VivIndex.timestamp.desc()).first()
    
    assert viv_index is not None
    print(f"DEBUG: Financial Score: {viv_index.financial_score}")
    print(f"DEBUG: Health Score: {viv_index.health_score}")
    print(f"DEBUG: Time Score: {viv_index.time_score}")
    
    assert viv_index.snapshot_reason == "Profile Update"
    assert viv_index.financial_score is not None
    # Depending on the scoring logic, these should be calculated. 
    # Provided input data might result in specific scores. We just check they are not None.
    
    db.close()

if __name__ == "__main__":
    setup_module(None)
    try:
        test_update_profile_identity()
        print("test_update_profile_identity PASSED")
        test_update_profile_onboarding_and_scores()
        print("test_update_profile_onboarding_and_scores PASSED")
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
