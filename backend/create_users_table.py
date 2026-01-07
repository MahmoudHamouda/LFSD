"""
Direct SQL script to create users table in CloudSQL
Using pg8000 to execute raw SQL since SQLAlchemy DDL doesn't work with pg8000
"""
from google.cloud.sql.connector import Connector
import pg8000

# Initialize Cloud SQL Connector
connector = Connector()

# Get connection
conn = connector.connect(
    "newprojectlfsd:us-central1:lfsd-postgres-prod",
    "pg8000",
    user="postgres",
    password="LfsdSecure2024!",
    db="lfsd"
)

cursor = conn.cursor()

print("=" * 60)
print("CREATING USERS TABLE")
print("=" * 60)

try:
    # Create users table with all necessary columns
    create_users_sql = """
    CREATE TABLE IF NOT EXISTS users (
        id VARCHAR PRIMARY KEY,
        email VARCHAR UNIQUE NOT NULL,
        auth0_id VARCHAR UNIQUE,
        hashed_password VARCHAR,
        profile_json JSONB,
        viv_preferences JSONB,
        onboarding_status VARCHAR DEFAULT 'NOT_STARTED',
        onboarding_step VARCHAR,
        onboarding_version INTEGER DEFAULT 1,
        password_reset_token VARCHAR,
        password_reset_expires TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS ix_users_email ON users(email);
    CREATE INDEX IF NOT EXISTS ix_users_auth0_id ON users(auth0_id);
    CREATE INDEX IF NOT EXISTS ix_users_password_reset_token ON users(password_reset_token);
    """
    
    print("\nExecuting CREATE TABLE statement...")
    cursor.execute(create_users_sql)
    conn.commit()
    
    print("✓ Users table created successfully!")
    
    # Verify table exists
    cursor.execute("""
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'users'
        ORDER BY ordinal_position
    """)
    
    columns = cursor.fetchall()
    print(f"\n✓ Verified {len(columns)} columns:")
    for col in columns:
        print(f"  - {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
    
    print("\n" + "=" * 60)
    print("TABLE CREATION COMPLETE!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    conn.rollback()
finally:
    cursor.close()
    conn.close()
    connector.close()
