
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def list_users():
    if not DATABASE_URL:
        print("DATABASE_URL not found.")
        return

    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT email, id, profile_json FROM users"))
        print("\n--- USERS ---")
        for row in result:
            print(f"Email: {row.email} | ID: {row.id} | Profile: {row.profile_json}")
        print("-------------\n")

if __name__ == "__main__":
    list_users()
