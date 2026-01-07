"""
Standalone Financial Data Seeder - 30 Day History (ORM Version)
Uses SQLAlchemy ORM to avoid datetime binding issues
"""
import sys
import os
import random
from datetime import datetime, timedelta

# Add backend to path for model imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.models import User, FinancialAccount, FinancialTransaction

DATABASE_URL = "postgresql+psycopg2://postgres:LfsdSecure2024!@136.119.201.13:5432/lfsd"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def seed_finance_30_days():
    print("=== SEEDING 30 DAYS OF FINANCIAL DATA (ORM) ===")
    
    session = Session()
    try:
        # Get finance user
        user = session.query(User).filter_by(email='finance@helm.com').first()
        if not user:
            print("ERROR: finance@helm.com user not found!")
            return
            
        print(f"Finance user ID: {user.id}")
        
        # 1. Create or get financial account
        account = session.query(FinancialAccount).filter_by(user_id=user.id).first()
        
        if account:
            print(f"Using existing account: {account.id}")
        else:
            account = FinancialAccount(
                user_id=user.id,
                name='Primary Checking',
                type='depository',
                balance=5000.00,
                currency='USD',
                institution_name='Chase Bank'
            )
            session.add(account)
            session.flush()  # Get the ID
            print(f"Created new account: {account.id}")
        
        # 2. Clear existing transactions
        deleted = session.query(FinancialTransaction).filter_by(user_id=user.id).delete()
        print(f"Cleared {deleted} existing transactions")
        session.commit()
        
        # 3. Create 30 days of transaction history
        print("Creating 30 days of transactions...")
        merchants = [
            ("Whole Foods", "Food & Dining"),
            ("Starbucks", "Food & Dining"),
            ("Shell Gas", "Transportation"),
            ("Amazon", "Shopping"),
            ("Netflix", "Entertainment"),
            ("Uber", "Transportation"),
            ("Target", "Shopping")
        ]
        
        transactions = []
        for day_offset in range(30):
            tx_date = datetime.utcnow() - timedelta(days=day_offset)
            
            # Weekly salary (every 7 days)
            if day_offset % 7 == 0:
                tx = FinancialTransaction(
                    account_id=account.id,
                    user_id=user.id,
                    amount=3000.00,
                    currency_code='USD',
                    transaction_date=tx_date,
                    description="Bi-weekly Salary",
                    merchant_name="Employer Inc",
                    category_primary="Income",
                    is_recurring=False
                )
                transactions.append(tx)
            
            # Daily expenses (1-2 per day)
            num_daily_tx = random.randint(1, 2)
            for _ in range(num_daily_tx):
                merchant, category = random.choice(merchants)
                amount = -random.uniform(10.0, 150.0)
                
                tx = FinancialTransaction(
                    account_id=account.id,
                    user_id=user.id,
                    amount=round(amount, 2),
                    currency_code='USD',
                    transaction_date=tx_date,
                    description=f"Purchase at {merchant}",
                    merchant_name=merchant,
                    category_primary=category,
                    is_recurring=False
                )
                transactions.append(tx)
        
        # Bulk insert
        session.bulk_save_objects(transactions)
        session.commit()
        print(f"✅ Successfully created {len(transactions)} transactions across 30 days")
        
        # 4. Verify the data
        print("\n=== VERIFICATION ===")
        total_tx = session.query(FinancialTransaction).filter_by(user_id=user.id).count()
        
        from sqlalchemy import func, cast, Date
        distinct_dates = session.query(
            func.count(func.distinct(cast(FinancialTransaction.transaction_date, Date)))
        ).filter_by(user_id=user.id).scalar()
        
        print(f"Total transactions: {total_tx}")
        print(f"Distinct dates: {distinct_dates}")
        
        # Sample recent transactions
        print("\nRecent transactions:")
        recent = session.query(FinancialTransaction).filter_by(user_id=user.id)\
            .order_by(FinancialTransaction.transaction_date.desc()).limit(5).all()
        
        for tx in recent:
            print(f"  {tx.merchant_name}: ${tx.amount:.2f} on {tx.transaction_date}")
            
    except Exception as e:
        session.rollback()
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    seed_finance_30_days()
    print("\n✅ SEEDING COMPLETE")
