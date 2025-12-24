
import sqlite3
import os

DB_PATH = "lfsd.db"

def reset():
    print(f"Connecting to {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    email = "alice@example.com"
    # Backend uses dummy hasher which compares plain text
    new_password = "password" 

    cursor.execute("UPDATE users SET hashed_password = ? WHERE email = ?", (new_password, email))
    
    if cursor.rowcount > 0:
        print(f"Successfully reset password for {email} to '{new_password}'")
    else:
        print(f"User {email} not found!")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    reset()
