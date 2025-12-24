import sqlite3
import os

def list_tables():
    db_paths = ['backend/lfsd_v2.db', './lfsd_v2.db']
    for path in db_paths:
        if os.path.exists(path):
            print(f"Checking database at {path}")
            conn = sqlite3.connect(path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"Tables: {tables}")
            conn.close()
        else:
            print(f"Database not found at {path}")

if __name__ == "__main__":
    list_tables()
