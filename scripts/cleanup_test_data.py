
import sqlite3
import os

DB_PATH = "lfsd.db"

def cleanup():
    print(f"Connecting to {DB_PATH} for cleanup...")
    if not os.path.exists(DB_PATH):
        print("Database not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Enable foreign keys - DISABLED to allow force cleanup of users
    # cursor.execute("PRAGMA foreign_keys = ON")

    target_email = "alice@example.com"
    target_password_hash = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW" # "password" hashed roughly, or we can just leave it if it exists.

    # Check if Alice exists
    cursor.execute("SELECT id FROM users WHERE email = ?", (target_email,))
    alice = cursor.fetchone()

    if not alice:
        print(f"Creating default user {target_email}...")
        # Create Alice
        # Note: minimal fields.
        cursor.execute("""
            INSERT INTO users (email, hashed_password, name, onboarding_status, onboarding_step)
            VALUES (?, ?, ?, 'COMPLETE', NULL)
        """, (target_email, target_password_hash, "Alice",))
        print("Created Alice.")
    else:
        print(f"User {target_email} exists. Retaining.")

    # Delete all others
    print("Deleting other users...")
    cursor.execute("DELETE FROM users WHERE email != ?", (target_email,))
    deleted_count = cursor.rowcount
    print(f"Deleted {deleted_count} other users.")

    conn.commit()
    conn.close()
    print("Cleanup complete.")

if __name__ == "__main__":
    cleanup()
