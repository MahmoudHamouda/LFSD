import os
import json
from sqlalchemy import create_engine, text

DB_URL = os.getenv("DATABASE_URL", "sqlite:///./lfsd_v2.db")

def verify():
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            print("--- VERIFYING FINANCE USER DATA ---")
            
            # 1. Get User
            user = conn.execute(text("SELECT id, email FROM users WHERE email='finance@helm.com'")).fetchone()
            if not user:
                print("User finance@helm.com NOT FOUND")
                return
            
            user_id, email = user
            print(f"User: {email} (ID: {user_id})")
            
            # 2. Check VivIndex (Overall Scores)
            viv = conn.execute(text(f"SELECT financial_score, health_score, time_score, timestamp FROM viv_indexes WHERE user_id='{user_id}' ORDER BY timestamp DESC LIMIT 1")).fetchone()
            if viv:
                print(f"\n[VivIndex] Latest Scores:")
                print(f"  Financial: {viv[0]}")
                print(f"  Health: {viv[1]}")
                print(f"  Time: {viv[2]}")
                print(f"  Timestamp: {viv[3]}")
            else:
                print("\n[VivIndex] NO SCORES FOUND")
                
            # 3. Check Financial Score (Detailed)
            fs = conn.execute(text(f"SELECT overall_score, cashflow_stability_score, bills_coverage_score, savings_rate_score, debt_load_score, discretionary_control_score, emergency_buffer_score, networth_momentum_score, investment_health_score FROM financial_scores WHERE user_id='{user_id}' ORDER BY timestamp DESC LIMIT 1")).fetchone()
            if fs:
                print(f"\n[FinancialScore] Breakdown:")
                print(f"  Overall: {fs[0]}")
                print(f"  Cashflow: {fs[1]}")
                print(f"  Bills: {fs[2]}")
                print(f"  Savings: {fs[3]}")
                print(f"  Debt: {fs[4]}")
                print(f"  Discretionary: {fs[5]}")
                print(f"  Emergency: {fs[6]}")
                print(f"  Networth: {fs[7]}")
                print(f"  Investments: {fs[8]}")
            else:
                 print("\n[FinancialScore] NO DETAIL SCORES FOUND")

            # 4. Check Counts
            tx_count = conn.execute(text(f"SELECT count(*) FROM transactions WHERE account_id IN (SELECT id FROM financial_accounts WHERE user_id='{user_id}')")).scalar()
            acc_count = conn.execute(text(f"SELECT count(*) FROM financial_accounts WHERE user_id='{user_id}'")).scalar()
            
            print(f"\n[Data Counts]")
            print(f"  Accounts: {acc_count}")
            print(f"  Transactions: {tx_count}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify()
