"""
Verify data in Cloud SQL for a specific user
"""

import os
os.environ["DATABASE_URL"] = "postgresql://lfsd_user:LFSDProd2026SecurePass!@136.119.201.13:5432/lfsd"

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

engine = create_engine(os.environ["DATABASE_URL"])
Session = sessionmaker(bind=engine)
session = Session()

# Check which users exist and their data
print("=" * 80)
print("CHECKING USER DATA IN CLOUD SQL")
print("=" * 80)

# List all users
result = session.execute(text("SELECT id, email, onboarding_status FROM users ORDER BY email;"))
users = result.fetchall()

print(f"\n📋 Total Users: {len(users)}")
print("-" * 80)

for user_id, email, status in users:
    print(f"\n👤 {email}")
    print(f"   ID: {user_id}")
    print(f"   Status: {status}")
    
    # Count related data
    accounts = session.execute(text("SELECT COUNT(*) FROM financial_accounts WHERE user_id = :uid"), {"uid": user_id}).scalar()
    transactions = session.execute(text("SELECT COUNT(*) FROM transactions WHERE user_id = :uid"), {"uid": user_id}).scalar()
    health = session.execute(text("SELECT COUNT(*) FROM health_daily_summaries WHERE user_id = :uid"), {"uid": user_id}).scalar()
    events = session.execute(text("SELECT COUNT(*) FROM calendar_events WHERE user_id = :uid"), {"uid": user_id}).scalar()
    goals = session.execute(text("SELECT COUNT(*) FROM life_goals WHERE user_id = :uid"), {"uid": user_id}).scalar()
    viv_index = session.execute(text("SELECT COUNT(*) FROM viv_indexes WHERE user_id = :uid"), {"uid": user_id}).scalar()
    
    print(f"   📊 Data:")
    print(f"      - Financial Accounts: {accounts}")
    print(f"      - Transactions: {transactions}")
    print(f"      - Health Records: {health}")
    print(f"      - Calendar Events: {events}")
    print(f"      - Life Goals: {goals}")
    print(f"      - VivIndex Records: {viv_index}")
    
    if viv_index > 0:
        scores = session.execute(
            text("SELECT financial_score, health_score, time_score FROM viv_indexes WHERE user_id = :uid ORDER BY timestamp DESC LIMIT 1"),
            {"uid": user_id}
        ).fetchone()
        if scores:
            print(f"      - Latest Scores: Finance={scores[0]}, Health={scores[1]}, Time={scores[2]}")

print("\n" + "=" * 80)

session.close()
