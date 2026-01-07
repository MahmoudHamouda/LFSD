"""
Check finance@helm.com specific data
"""

import os
os.environ["DATABASE_URL"] = "postgresql://lfsd_user:LFSDProd2026SecurePass!@136.119.201.13:5432/lfsd"

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

engine = create_engine(os.environ["DATABASE_URL"])
Session = sessionmaker(bind=engine)
session = Session()

print("=" * 80)
print("FINANCE@HELM.COM DATA CHECK")
print("=" * 80)

# Get user
user = session.execute(
    text("SELECT id, email, onboarding_status, profile_json FROM users WHERE email = 'finance@helm.com'")
).fetchone()

if not user:
    print("❌ User not found!")
    session.close()
    exit(1)

user_id = user[0]
print(f"\n👤 User: {user[1]}")
print(f"   ID: {user_id}")
print(f"   Status: {user[2]}")
print(f"   Profile: {user[3]}")

# Check VivIndex
print("\n📊 VivIndex Scores:")
scores = session.execute(
    text("""
        SELECT financial_score, health_score, time_score, timestamp 
        FROM viv_indexes 
        WHERE user_id = :uid 
        ORDER BY timestamp DESC 
        LIMIT 1
    """),
    {"uid": user_id}
).fetchone()

if scores:
    print(f"   Financial: {scores[0]}")
    print(f"   Health: {scores[1]}")
    print(f"   Time: {scores[2]}")
    print(f"   Timestamp: {scores[3]}")
else:
    print("   ❌ NO VIVINDEX RECORDS FOUND!")

# Check Financial Accounts
print("\n💰 Financial Accounts:")
accounts = session.execute(
    text("SELECT id, institution_name, account_type, current_balance FROM financial_accounts WHERE user_id = :uid"),
    {"uid": user_id}
).fetchall()

if accounts:
    for acc_id, inst, acc_type, balance in accounts:
        print(f"   - {inst} ({acc_type}): ${balance:,.2f}")
        print(f"     ID: {acc_id}")
else:
    print("   ❌ NO ACCOUNTS FOUND!")

# Check Transactions
print("\n📝 Transactions:")
txn_count = session.execute(
    text("SELECT COUNT(*) FROM transactions WHERE user_id = :uid"),
    {"uid": user_id}
).scalar()
print(f"   Total: {txn_count}")

if txn_count > 0:
    recent = session.execute(
        text("""
            SELECT amount, description, transaction_date 
            FROM transactions 
            WHERE user_id = :uid 
            ORDER BY transaction_date DESC 
            LIMIT 5
        """),
        {"uid": user_id}
    ).fetchall()
    
    print("   Recent:")
    for amount, desc, date in recent:
        print(f"     {date}: ${amount:,.2f} - {desc}")

# Check Goals
print("\n🎯 Life Goals:")
goals = session.execute(
    text("SELECT title, target_amount, saved_amount FROM life_goals WHERE user_id = :uid"),
    {"uid": user_id}
).fetchall()

if goals:
    for title, target, saved in goals:
        print(f"   - {title}: ${saved:,.2f} / ${target:,.2f}")
else:
    print("   ❌ NO GOALS FOUND!")

# Check Financial Score
print("\n📈 Financial Score Breakdown:")
fin_score = session.execute(
    text("""
        SELECT overall_score, cashflow_stability_score, savings_rate_score 
        FROM financial_scores 
        WHERE user_id = :uid 
        ORDER BY timestamp DESC 
        LIMIT 1
    """),
    {"uid": user_id}
).fetchone()

if fin_score:
    print(f"   Overall: {fin_score[0]}")
    print(f"   Cashflow: {fin_score[1]}")
    print(f"   Savings Rate: {fin_score[2]}")
else:
    print("   ❌ NO FINANCIAL SCORE FOUND!")

print("\n" + "=" * 80)

session.close()
