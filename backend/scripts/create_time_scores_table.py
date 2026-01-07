"""
Create time_scores table in database
Uses SQLAlchemy to create the table based on TimeScore model
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine
from models.models import Base, TimeScore

DATABASE_URL = "postgresql+psycopg2://postgres:LfsdSecure2024!@136.119.201.13:5432/lfsd"

def create_time_scores_table():
    print("=== CREATING TIME_SCORES TABLE ===")
    
    engine = create_engine(DATABASE_URL)
    
    try:
        # Create only the time_scores table
        TimeScore.__table__.create(engine, checkfirst=True)
        print("✅ time_scores table created successfully")
        
        # Verify table exists
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if 'time_scores' in tables:
            print("✅ Verified: time_scores table exists in database")
            
            # Show columns
            columns = inspector.get_columns('time_scores')
            print(f"\nTable has {len(columns)} columns:")
            for col in columns:
                print(f"  - {col['name']}: {col['type']}")
        else:
            print("❌ time_scores table not found after creation")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_time_scores_table()
    print("\n✅ MIGRATION COMPLETE")
