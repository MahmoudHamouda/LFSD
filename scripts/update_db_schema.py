import sqlite3
from database import engine, Base
import models
from sqlalchemy import inspect, text

def update_schema():
    print("Updating schema...")
    
    # 1. Create new tables (life_goals)
    Base.metadata.create_all(bind=engine)
    print("Created new tables (if any).")
    
    # 2. Add columns to users table if missing
    inspector = inspect(engine)
    columns = [c['name'] for c in inspector.get_columns('users')]
    
    new_columns = {
        'viv_financial_score': 'INTEGER DEFAULT 50',
        'viv_health_score': 'INTEGER DEFAULT 50',
        'viv_time_score': 'INTEGER DEFAULT 50'
    }
    
    with engine.connect() as conn:
        for col_name, col_type in new_columns.items():
            if col_name not in columns:
                print(f"Adding column {col_name} to users table...")
                try:
                    conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    print(f"Added {col_name}.")
                except Exception as e:
                    print(f"Error adding {col_name}: {e}")
            else:
                print(f"Column {col_name} already exists.")

if __name__ == "__main__":
    update_schema()
