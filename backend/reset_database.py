"""
Database Reset Script
Drops all existing tables and recreates them with the current schema
"""
from models.database import engine, Base, get_db
from models.models import *  # Import all models to register them
from sqlalchemy import text
import sys

def reset_database():
    """
    Drop all tables and recreate with current schema
    """
    print("=" * 60)
    print("DATABASE RESET SCRIPT")
    print("=" * 60)
    
    try:
        # Step 1: Drop all tables
        print("\n[1/3] Dropping all existing tables...")
        Base.metadata.drop_all(bind=engine)
        print("✓ All tables dropped successfully")
        
        # Step 2: Create all tables with current schema
        print("\n[2/3] Creating tables with new schema...")
        Base.metadata.create_all(bind=engine)
        print("✓ All tables created successfully")
        
        # Step 3: Verify tables exist
        print("\n[3/3] Verifying database schema...")
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' ORDER BY table_name"
            ))
            tables = [row[0] for row in result]
            
        print(f"✓ Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table}")
        
        # Check if auth0_id was added to users table
        print("\n[VERIFICATION] Checking users table schema...")
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT column_name, data_type, is_nullable "
                "FROM information_schema.columns "
                "WHERE table_name = 'users' "
                "ORDER BY ordinal_position"
            ))
            columns = [(row[0], row[1], row[2]) for row in result]
        
        print("Users table columns:")
        for col_name, col_type, nullable in columns:
            print(f"  - {col_name}: {col_type} ({'NULL' if nullable == 'YES' else 'NOT NULL'})")
        
        auth0_id_exists = any(col[0] == 'auth0_id' for col in columns)
        if auth0_id_exists:
            print("\n✅ SUCCESS: auth0_id field added to users table")
        else:
            print("\n⚠️  WARNING: auth0_id field NOT found in users table")
        
        print("\n" + "=" * 60)
        print("DATABASE RESET COMPLETE!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Run seed_users.py to populate test data")
        print("2. Deploy backend to Cloud Run")
        print("3. Test Auth0 login flow")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = reset_database()
    sys.exit(exit_code)
