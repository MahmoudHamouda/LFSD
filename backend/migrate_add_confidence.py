import sqlite3

def migrate():
    print("Running migration...")
    conn = sqlite3.connect('lfsd_v2.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("ALTER TABLE viv_indexes ADD COLUMN confidence FLOAT DEFAULT 1.0")
        conn.commit()
        print("Migration successful: Added 'confidence' column.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
             print("Column 'confidence' already exists.")
        else:
             print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
