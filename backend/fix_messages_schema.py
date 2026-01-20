import pg8000
import sys

def fix_schema():
    print("Connecting to DB...")
    try:
        conn = pg8000.connect(
            user="lfsd_app",
            password="SecurePass123",
            host="136.119.201.13",
            database="lfsd"
        )
        cursor = conn.cursor()
        
        print("Adding usage columns to messages table...")
        
        statements = [
            "ALTER TABLE messages ADD COLUMN IF NOT EXISTS user_id VARCHAR",
            "ALTER TABLE messages ADD COLUMN IF NOT EXISTS input_tokens INTEGER",
            "ALTER TABLE messages ADD COLUMN IF NOT EXISTS output_tokens INTEGER",
            "ALTER TABLE messages ADD COLUMN IF NOT EXISTS model_used VARCHAR"
        ]
        
        for sql in statements:
            print(f"Executing: {sql}")
            cursor.execute(sql)
            
        conn.commit()
        print("Schema updated successfully.")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    fix_schema()
