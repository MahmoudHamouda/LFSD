from backend.models.database import engine
from sqlalchemy import text

print("Connecting to database...")
with engine.connect() as conn:
    print("Dropping old foreign key...")
    try:
        conn.execute(text('ALTER TABLE subscriptions DROP CONSTRAINT IF EXISTS subscriptions_user_id_fkey;'))
        conn.commit()
    except Exception as e:
        print(f"Error dropping constraint: {e}")

    print("Adding new foreign key...")
    try:
        conn.execute(text('ALTER TABLE subscriptions ADD CONSTRAINT subscriptions_user_id_fkey FOREIGN KEY (user_id) REFERENCES users_v2(id) ON DELETE CASCADE;'))
        conn.commit()
        print("Done!")
    except Exception as e:
        print(f"Error adding constraint: {e}")

print("Fix completed.")
