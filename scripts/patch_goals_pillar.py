
import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load settings from .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def patch_goals_pillar():
    if not DATABASE_URL:
        print("DATABASE_URL not found in environment.")
        return

    print(f"Connecting to database...")
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Enable autocommit for ALTER TABLE
        conn = conn.execution_options(isolation_level="AUTOCOMMIT")

        print("Adding 'pillar' column to 'life_goals' table...")
        try:
            # Add the 'pillar' column with a default value of 'finance'
            conn.execute(text("ALTER TABLE life_goals ADD COLUMN pillar VARCHAR DEFAULT 'finance'"))
            print("Successfully added 'pillar' column to 'life_goals'.")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("Column 'pillar' already exists in 'life_goals'.")
            else:
                print(f"Error adding column: {e}")

    print("Database patch operation finished.")

if __name__ == "__main__":
    patch_goals_pillar()
