import os
import sys
import pytest
import asyncio
from datetime import datetime, timedelta

# Add backend to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../backend")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models.database import Base
# Import all models to register them with Base.metadata
from backend.models.models import User, VivIndex, FinancialAccount, FinancialTransaction, CalendarEvent
from backend.models.growth_models import Subscription
from backend.models.intelligence_models import PipelineTraceRecord, DecisionRecord
from backend.models.logging_models import SystemLog, AuditLog, ActivityFeed

from backend.services.gemini_service import GeminiService

@pytest.fixture(scope="module")
def db_session():
    # Setup local SQLite in-memory database
    engine = create_engine("sqlite:///:memory:")
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    
    # Seed users and data
    # 1. Finance User
    finance_user = User(
        id="finance-user-id",
        email="finance@helm.com",
        profile_json={"name": "Finance Persona", "type": "finance"},
        onboarding_status="COMPLETE"
    )
    db.add(finance_user)
    
    sub1 = Subscription(user_id=finance_user.id, plan_id="tier_pro", status="active")
    db.add(sub1)
    
    acct = FinancialAccount(
        id="acct-1", user_id=finance_user.id, institution_name="Checking", account_type="checking", current_balance=15000.0
    )
    db.add(acct)
    
    t1 = FinancialTransaction(
        id="tx-1", user_id=finance_user.id, account_id="acct-1",
        amount=250.0, category_primary="Food and Drink", transaction_date=datetime.utcnow() - timedelta(days=1)
    )
    t2 = FinancialTransaction(
        id="tx-2", user_id=finance_user.id, account_id="acct-1",
        amount=1000.0, category_primary="Rent", transaction_date=datetime.utcnow() - timedelta(days=5)
    )
    db.add_all([t1, t2])
    
    # 2. Time User
    time_user = User(
        id="time-user-id",
        email="time@helm.com",
        profile_json={"name": "Time Persona", "type": "time"},
        onboarding_status="COMPLETE"
    )
    db.add(time_user)
    
    sub2 = Subscription(user_id=time_user.id, plan_id="tier_pro", status="active")
    db.add(sub2)
    
    ev1 = CalendarEvent(
        id="ev-1", user_id=time_user.id, title="Deep Work",
        start_time=datetime.utcnow() - timedelta(hours=4), end_time=datetime.utcnow() - timedelta(hours=2)
    )
    db.add(ev1)
    
    # 3. Health User
    health_user = User(
        id="health-user-id",
        email="health@helm.com",
        profile_json={"name": "Health Persona", "type": "health"},
        onboarding_status="COMPLETE"
    )
    db.add(health_user)
    
    sub3 = Subscription(user_id=health_user.id, plan_id="tier_pro", status="active")
    db.add(sub3)
    
    # Add initial VivIndex
    db.add_all([
        VivIndex(user_id=finance_user.id, financial_score=85, health_score=75, time_score=80),
        VivIndex(user_id=time_user.id, financial_score=80, health_score=80, time_score=90),
        VivIndex(user_id=health_user.id, financial_score=75, health_score=85, time_score=85),
    ])
    
    db.commit()
    yield db
    db.close()

import json

@pytest.mark.asyncio
async def test_productivity_response(db_session):
    service = GeminiService(db_session)
    context = {"user_id": "time-user-id"}
    history = [{"role": "user", "content": "How much focus time did I have last week?"}]
    
    response = await service.generate_response(history, context)
    assert response is not None
    res_data = json.loads(response)
    
    response_text = res_data.get("text", "")
    assert len(response_text) > 0
    assert "error" not in response_text.lower() or "503" not in response_text

@pytest.mark.asyncio
async def test_financial_response(db_session):
    service = GeminiService(db_session)
    context = {"user_id": "finance-user-id"}
    history = [{"role": "user", "content": "Can I afford to spend $500 on a watch?"}]
    
    response = await service.generate_response(history, context)
    assert response is not None
    res_data = json.loads(response)
    
    response_text = res_data.get("text", "")
    assert len(response_text) > 0
    # Check if the response contains financial advice keywords or if it warns about budgeting/affording
    assert any(k in response_text.lower() for k in ["watch", "spend", "afford", "budget", "money", "cost", "financial", "purchase", "saving"])

@pytest.mark.asyncio
async def test_mobility_response(db_session):
    service = GeminiService(db_session)
    context = {
        "user_id": "health-user-id",
        "location": {"lat": 25.2048, "lng": 55.2708}
    }
    history = [{"role": "user", "content": "How much is an Uber to the Dubai Marina?"}]
    
    response = await service.generate_response(history, context)
    assert response is not None
    res_data = json.loads(response)
    
    response_text = res_data.get("text", "")
    assert len(response_text) > 0
    assert any(k in response_text.lower() for k in ["uber", "careem", "bolt", "price", "ride", "options", "estimate"])

