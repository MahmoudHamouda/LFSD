
import sqlite3
import os

DB_PATH = "lfsd.db"

def update_status():
    print(f"Connecting to {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    email = "alice@example.com"
    status = "COMPLETE"

    cursor.execute("UPDATE users SET onboarding_status = ? WHERE email = ?", (status, email))
    
    if cursor.rowcount > 0:
        print(f"Successfully updated status for {email} to '{status}'")
    else:
        print(f"User {email} not found!")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    update_status()
