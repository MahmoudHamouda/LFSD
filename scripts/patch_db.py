
import sqlite3
import os

DB_PATH = "lfsd_v2.db"

def patch_database():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found. Skipping patch (init_db will create it).")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check existing columns
        cursor.execute("PRAGMA table_info(financial_scores)")
        columns_info = cursor.fetchall()
        existing_columns = [col[1] for col in columns_info]
        
        new_columns = [
            ("total_monthly_income", "FLOAT DEFAULT 0"),
            ("total_monthly_expenses", "FLOAT DEFAULT 0"),
            ("total_monthly_bills", "FLOAT DEFAULT 0"),
            ("total_monthly_savings", "FLOAT DEFAULT 0"),
            ("total_assets_value", "FLOAT DEFAULT 0")
        ]
        
        for col_name, col_type in new_columns:
            if col_name not in existing_columns:
                print(f"Adding column {col_name}...")
                cursor.execute(f"ALTER TABLE financial_scores ADD COLUMN {col_name} {col_type}")
            else:
                print(f"Column {col_name} already exists.")
                
        conn.commit()
        print("Database patch completed successfully.")
        
    except Exception as e:
        print(f"Error patching database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    patch_database()
