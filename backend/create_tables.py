"""
Script to create all database tables in CloudSQL using SQLAlchemy
"""
from google.cloud.sql.connector import Connector
from sqlalchemy import create_engine
from models.database import Base
from models.models import *  # Import all models

# Initialize Cloud SQL Connector
connector = Connector()

def getconn():
    """Create database connection using Cloud SQL Connector"""
    conn = connector.connect(
        "newprojectlfsd:us-central1:lfsd-postgres-prod",
        "pg8000",  # Use pg8000 for this one-time operation
        user="postgres",
        password="LfsdSecure2024!",
        db="lfsd"
    )
    return conn

# Create engine
engine = create_engine(
    "postgresql+pg8000://",
    creator=getconn,
)

print("=" * 60)
print("CREATING ALL DATABASE TABLES")
print("=" * 60)

try:
    # Create all tables
    print("\nCreating tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ All tables created successfully!")
    
    # List created tables
    print("\nVerifying tables...")
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"\n✓ Found {len(tables)} tables:")
    for table in sorted(tables):
        print(f"  - {table}")
    
    print("\n" + "=" * 60)
    print("DATABASE SCHEMA CREATION COMPLETE!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    connector.close()
