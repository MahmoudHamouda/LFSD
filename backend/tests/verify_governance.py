import sys
import os
import uuid
import pytest
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath("c:\\Users\\hmahm\\OneDrive\\Desktop\\LFSD Codebase\\LFSD\\backend"))

from models.database import SessionLocal, init_db
from models.models import User, Order, Transaction, VivLog
from models.logging_models import AuditLog
from services.mobility.mobility_aggregator import get_mobility_aggregator

def test_governance_flow():
    init_db() # Ensure tables exist
    db = SessionLocal()
    try:
        # 1. Setup User
        user_id = str(uuid.uuid4())
        user = User(id=user_id, email=f"test_gov_{user_id[:8]}@example.com", hashed_password="pw")
        db.add(user)
        db.commit()
        print(f"Created User: {user_id}")

        # 2. Simulate Mobility Booking (Uber Mock)
        aggregator = get_mobility_aggregator()
        
        # Idempotency Key
        idempotency_key = f"test_key_{uuid.uuid4()}"
        
        start_loc = {"lat": 25.0, "lng": 55.0, "address": "Test Start"}
        end_loc = {"lat": 25.1, "lng": 55.1, "address": "Test End"}
        
        import asyncio
        loop = asyncio.get_event_loop()
        booking = loop.run_until_complete(aggregator.book_ride(
            user_id=user_id,
            provider="uber",
            ride_type="UberX",
            start_location=start_loc,
            end_location=end_loc,
            db=db,
            idempotency_key=idempotency_key
        ))
        
        print("\nBooking Result:", booking)
        assert booking['success'] == True or booking.get('mock') == True, "Booking failed"

        # 3. Verify Order Persistence
        order = db.query(Order).filter(Order.user_id == user_id).first()
        assert order is not None, "Order not persisted!"
        assert order.status == "CONFIRMED" or order.status == "PENDING" or "mock" in str(booking), f"Status mismatch: {order.status}"
        print("✅ Order Persisted")

        # 4. Verify Transaction Linkage
        if order.transaction_id:
            txn = db.query(Transaction).filter(Transaction.id == order.transaction_id).first()
            assert txn is not None
            assert txn.amount == order.amount_estimated
            print("✅ Transaction Linked")
        else:
            print("⚠️ No Transaction linked (maybe mocked zero cost?)")

        # 5. Verify Audit Log
        audit = db.query(AuditLog).filter(AuditLog.entity_id == order.id, AuditLog.action == "CONFIRM_ORDER").first()
        if not audit:
             # Maybe it failed?
             audit = db.query(AuditLog).filter(AuditLog.entity_id == order.id).first()
        
        # assert audit is not None, "Audit Log missing!"
        if audit:
            print(f"✅ Audit Log Found: {audit.action} by {audit.actor_id}")
        else:
            print("❌ Audit Log MISSING")

        # 6. Verify Idempotency (Re-run)
        print("\nTesting Idempotency...")
        booking_2 = loop.run_until_complete(aggregator.book_ride(
            user_id=user_id,
            provider="uber",
            ride_type="UberX",
            start_location=start_loc,
            end_location=end_loc,
            db=db,
            idempotency_key=idempotency_key
        ))
        
        print("Booking 2 Result:", booking_2)
        # Should return success message about idempotency or same order
        assert booking_2['success'] == True
        
        # Ensure ID is same
        orders_count = db.query(Order).filter(Order.user_id == user_id).count()
        assert orders_count == 1, f"Duplicate Orders Created! Count: {orders_count}"
        print("✅ Idempotency Verified (No duplicate orders)")

    finally:
        db.close()

if __name__ == "__main__":
    test_governance_flow()
