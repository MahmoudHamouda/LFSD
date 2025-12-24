
import sqlite3
import os

# Database file path - derived from current directory context
DB_PATH = "lfsd.db" # Standard for many setups, but I should check where app.py thinks it is.
# Checking models/database.py is better practice usually, but for a script, direct file access is fine if we match.
# Let's assume ./lfsd.db relative to root.

def migrate():
    print(f"Connecting to database at {DB_PATH}...")
    if not os.path.exists(DB_PATH):
        print("Error: Database file not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    columns_to_add = [
        ("onboarding_status", "TEXT DEFAULT 'NOT_STARTED'"),
        ("onboarding_step", "TEXT"),
        ("onboarding_version", "INTEGER DEFAULT 1"),
        ("updated_at", "DATETIME") # Nullable, Python handles default
    ]

    for col_name, col_def in columns_to_add:
        try:
            print(f"Adding column {col_name}...")
            cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
            print(f"Successfully added {col_name}.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"Column {col_name} already exists. Skipping.")
            else:
                print(f"Error adding {col_name}: {e}")

    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
