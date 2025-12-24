
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def patch_postgres():
    if not DATABASE_URL:
        print("DATABASE_URL not found in environment.")
        return

    print(f"Connecting to database...")
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        conn = conn.execution_options(isolation_level="AUTOCOMMIT")
        
        # New columns to add
        new_columns = [
            ("total_monthly_income", "FLOAT DEFAULT 0"),
            ("total_monthly_expenses", "FLOAT DEFAULT 0"),
            ("total_monthly_bills", "FLOAT DEFAULT 0"),
            ("total_monthly_savings", "FLOAT DEFAULT 0"),
            ("total_assets_value", "FLOAT DEFAULT 0")
        ]
        
        print("Checking columns...")
        
        # Check existing columns directly from information_schema
        # Note: simplistic check, if fails we catch it.
        
        for col_name, col_type in new_columns:
            try:
                # Attempt to add column. Postgres will error if it exists.
                # We can check existence or just try/except. 
                # Better to use "IF NOT EXISTS" logic but Postgres ADD COLUMN doesn't support IF NOT EXISTS natively in older versions without a block.
                # Easiest is try/except.
                print(f"Attempting to add {col_name}...")
                conn.execute(text(f"ALTER TABLE financial_scores ADD COLUMN {col_name} {col_type}"))
                print(f"Added {col_name}.")
            except Exception as e:
                # Check for "already exists" error
                if "already exists" in str(e):
                    print(f"Column {col_name} already exists.")
                else:
                    print(f"Error adding {col_name}: {e}")

    print("Postgres patch process finished.")

if __name__ == "__main__":
    patch_postgres()
