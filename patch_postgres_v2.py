
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def patch_postgres_schema():
    if not DATABASE_URL:
        print("DATABASE_URL not found.")
        return

    print("Connecting to database...")
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        conn = conn.execution_options(isolation_level="AUTOCOMMIT")

        # 1. Add RecurringBill Table
        print("Checking for recurring_bills table...")
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS recurring_bills (
                    id VARCHAR PRIMARY KEY,
                    user_id VARCHAR NOT NULL REFERENCES users(id),
                    name VARCHAR NOT NULL,
                    amount FLOAT NOT NULL,
                    cadence VARCHAR DEFAULT 'monthly',
                    next_due_date DATE,
                    category VARCHAR,
                    is_verified BOOLEAN DEFAULT FALSE
                )
            """))
            # Index
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_recurring_bills_user_id ON recurring_bills (user_id)"))
            print("RecurringBills table checked/created.")
        except Exception as e:
            print(f"Error creating recurring_bills: {e}")

        # 2. Update LifeGoal Table
        print("Updating life_goals table...")
        cols_to_add = [
            ("target_date", "TIMESTAMP"),
            ("type", "VARCHAR"),
            ("monthly_contribution_target", "FLOAT DEFAULT 0")
        ]
        for col, type_ in cols_to_add:
            try:
                conn.execute(text(f"ALTER TABLE life_goals ADD COLUMN {col} {type_}"))
                print(f"Added {col} to life_goals")
            except Exception as e:
                # likely exists
                if "already exists" not in str(e):
                    print(f"Error adding {col} to life_goals: {e}")

        # 3. Update FinancialScore Columns (8 sub-scores)
        print("Updating financial_scores table...")
        new_scores = [
            "cashflow_stability_score",
            "bills_coverage_score",
            "discretionary_control_score",
            "savings_rate_score",
            "emergency_buffer_score",
            "debt_load_score",
            "networth_momentum_score",
            "investment_health_score"
        ]
        
        for sc in new_scores:
            try:
                conn.execute(text(f"ALTER TABLE financial_scores ADD COLUMN {sc} FLOAT DEFAULT 0"))
                print(f"Added {sc}")
            except Exception as e:
                if "already exists" not in str(e):
                    print(f"Error adding {sc}: {e}")

    print("Schema patch complete.")

if __name__ == "__main__":
    patch_postgres_schema()
