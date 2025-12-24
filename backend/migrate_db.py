from models.database import engine
from sqlalchemy import text

def migrate():
    print("Starting migration...")
    try:
        with engine.connect() as conn:
            # Add confidence column to viv_indexes if it doesn't exist
            conn.execute(text("ALTER TABLE viv_indexes ADD COLUMN IF NOT EXISTS confidence FLOAT DEFAULT 1.0;"))
            
            # Add password reset columns to users table
            # PostgreSQL doesn't support ADD COLUMN IF NOT EXISTS for multiple columns easily in older versions, 
            # but we can do it one by one or use a DO block.
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN password_reset_token VARCHAR;"))
                print("Added password_reset_token column.")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("password_reset_token column already exists.")
                else:
                    print(f"Error adding password_reset_token: {e}")

            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN password_reset_expires TIMESTAMP;"))
                print("Added password_reset_expires column.")
            except Exception as e:
                if "already exists" in str(e).lower():
                    print("password_reset_expires column already exists.")
                else:
                    print(f"Error adding password_reset_expires: {e}")

            try:
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_password_reset_token ON users (password_reset_token);"))
                print("Created index for password_reset_token.")
            except Exception as e:
                print(f"Error creating index: {e}")

            conn.commit()
            print("Migration successful.")
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
