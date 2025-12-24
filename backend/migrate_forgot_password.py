from models.database import engine
from sqlalchemy import text

def migrate():
    print("Starting migration to add password reset columns...")
    try:
        with engine.begin() as conn:
            # SQLite syntax for adding columns
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN password_reset_token VARCHAR;"))
                print("Added password_reset_token column.")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    print("password_reset_token column already exists.")
                else:
                    print(f"Error adding password_reset_token: {e}")
            
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN password_reset_expires DATETIME;"))
                print("Added password_reset_expires column.")
            except Exception as e:
                if "duplicate column name" in str(e).lower():
                    print("password_reset_expires column already exists.")
                else:
                    print(f"Error adding password_reset_expires: {e}")
            
            # Create index for token
            try:
                conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_password_reset_token ON users (password_reset_token);"))
                print("Created index for password_reset_token.")
            except Exception as e:
                print(f"Error creating index: {e}")
            
        print("Migration process finished.")
    except Exception as e:
        print(f"Migration failed at top level: {e}")

if __name__ == "__main__":
    migrate()
