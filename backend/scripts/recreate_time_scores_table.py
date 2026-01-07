"""
Drop and recreate time_scores table with correct schema
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine, text
from models.models import TimeScore

DATABASE_URL = "postgresql+psycopg2://postgres:LfsdSecure2024!@136.119.201.13:5432/lfsd"

def recreate_time_scores_table():
    print("=== RECREATING TIME_SCORES TABLE ===")
    
    engine = create_engine(DATABASE_URL)
    
    try:
        # Drop existing table
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS time_scores CASCADE"))
            conn.commit()
        print("✅ Dropped old time_scores table")
        
        # Create new table with correct schema
        TimeScore.__table__.create(engine, checkfirst=False)
        print("✅ Created new time_scores table")
        
        # Verify columns
        from sqlalchemy import inspect
        inspector = inspect(engine)
        columns = inspector.get_columns('time_scores')
        
        print(f"\nTable has {len(columns)} columns:")
        for col in columns:
            print(f"  - {col['name']}: {col['type']}")
        
        # Check for new columns
        column_names = [col['name'] for col in columns]
        expected_columns = ['schedule_coverage_score', 'planning_habit_score', 'focus_blocks_score']
        
        if all(col in column_names for col in expected_columns):
            print("\n✅ Verified: Table has correct new schema")
        else:
            print("\n❌ Warning: Table may have old schema")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    recreate_time_scores_table()
    print("\n✅ MIGRATION COMPLETE")
