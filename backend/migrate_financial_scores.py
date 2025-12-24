from models.database import engine
from sqlalchemy import text

def migrate():
    print("Starting financial scores migration...")
    columns = [
        "cashflow_stability_score",
        "bills_coverage_score",
        "discretionary_control_score",
        "savings_rate_score",
        "emergency_buffer_score",
        "debt_load_score",
        "networth_momentum_score",
        "investment_health_score"
    ]
    
    with engine.connect() as conn:
        for col in columns:
            try:
                # Attempt to add column
                conn.execute(text(f"ALTER TABLE financial_scores ADD COLUMN {col} FLOAT DEFAULT 0.0;"))
                print(f"Added {col}.")
            except Exception as e:
                # Handle cases where column already exists
                if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                    print(f"Column {col} already exists.")
                else:
                    print(f"Error adding {col}: {e}")
        
        # Also ensure 'time_window' and 'data_sources_json' exist as they were part of the update
        try:
            conn.execute(text("ALTER TABLE financial_scores ADD COLUMN time_window VARCHAR DEFAULT 'last_3_months';"))
            print("Added time_window.")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                print("Column time_window already exists.")
            else:
                print(f"Error adding time_window: {e}")

        try:
            conn.execute(text("ALTER TABLE financial_scores ADD COLUMN data_sources_json JSON;"))
            print("Added data_sources_json.")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                print("Column data_sources_json already exists.")
            else:
                print(f"Error adding data_sources_json: {e}")

        conn.commit()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
