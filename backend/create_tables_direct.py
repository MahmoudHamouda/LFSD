import sys
import os

# Ensure backend directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from models.models import Base
from sqlalchemy import text

# Direct TCP URL (Prod)
DB_URL = "postgresql+psycopg2://postgres:LfsdSecure2024!@136.119.201.13:5432/lfsd"

def create_tables():
    print("--- CREATING TABLES (DIRECT TCP) ---")
    try:
        engine = create_engine(DB_URL)
        
        # Test connection
        with engine.connect() as conn:
            print("Connection successful.")
            
        print("Creating all tables via SQLAlchemy...")
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully.")
        
    except Exception as e:
        print(f"Error creating tables: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_tables()
