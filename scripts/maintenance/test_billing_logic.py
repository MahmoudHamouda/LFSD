import sys
import os
from unittest.mock import MagicMock

# 1. Setup Path and Mocks
sys.path.append(os.path.abspath(os.path.join(os.getcwd(), "backend")))
sys.modules["google.cloud"] = MagicMock()
sys.modules["google.cloud.sql"] = MagicMock()
sys.modules["pg8000"] = MagicMock()
sys.modules["jose"] = MagicMock()

# 2. Setup Memory DB
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
Base = declarative_base()

# 3. Patch models.database
class DummyDBModule:
    engine = test_engine
    SessionLocal = TestingSessionLocal
    Base = Base
    def get_db(self):
        db = TestingSessionLocal()
        try: yield db 
        finally: db.close()
    def init_db(self): pass

dummy_db = DummyDBModule()
# Patch all possible import paths
sys.modules["models.database"] = dummy_db
sys.modules["backend.models.database"] = dummy_db

# 4. Import Models and Service
import backend.models.models as models
from backend.models.models import User, DBMessage
from backend.models.growth_models import Subscription
from backend.models.growth_schemas import PlanId
from backend.services.billing_service import BillingService
from datetime import datetime

# Initialize Tables
# We need to use the actual Base from backend.models.database if we want the actual models
# But here we just mock it for a simple logic test
from backend.models.database import Base as RealBase
RealBase.metadata.create_all(bind=test_engine)

def test_billing_aggregation():
    db = TestingSessionLocal()
    
    # 1. Create a user
    user = User(id="user_test_1", email="billing@test.com", role="user")
    db.add(user)
    
    # 2. Add a Pro subscription ($9.99)
    sub = Subscription(
        user_id=user.id,
        plan_id=PlanId.PRO,
        status="active",
        current_period_start=datetime.utcnow(),
        current_period_end=datetime.utcnow()
    )
    db.add(sub)
    
    # 3. Add AI usage (100k input, 50k output)
    # Price: $0.075/1M in, $0.30/1M out
    # 100k * 0.000000075 = $0.0075
    # 50k * 0.00000030 = $0.015
    # Total AI Cost = $0.0225
    msg = DBMessage(
        id="msg_1",
        conversation_id="conv_1",
        user_id=user.id,
        role="assistant",
        content="Test",
        input_tokens=100000,
        output_tokens=50000
    )
    db.add(msg)
    
    db.commit()
    
    service = BillingService(db)
    summary = service.get_overall_summary()
    
    print(f"Summary Metrics: {summary['metrics']}")
    print(f"Summary Finance: {summary['total_revenue']} Rev, {summary['total_cost']} Cost, {summary['profit']} Profit")
    
    assert summary["total_revenue"] == 9.99
    assert summary["total_cost"] == 0.0225
    assert summary["profit"] == 9.97
    
    reconciliation = service.get_customer_reconciliation()
    print(f"First Customer Reconciliation: {reconciliation[0]}")
    assert reconciliation[0]["revenue"] == 9.99
    assert reconciliation[0]["cost"] == 0.0225
    
    print("Billing Logic Test PASSED!")
    db.close()

if __name__ == "__main__":
    try:
        test_billing_aggregation()
    except Exception as e:
        import traceback
        traceback.print_exc()
        sys.exit(1)
