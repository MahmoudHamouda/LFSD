import os
from sqlalchemy import create_engine, text
from google.cloud.sql.connector import Connector
import pg8000

def getconn():
    instance_connection_name = os.environ.get("INSTANCE_CONNECTION_NAME")
    db_user = os.environ.get("DB_USER")
    db_pass = os.environ.get("DB_PASS")
    db_name = os.environ.get("DB_NAME")
    
    unix_socket_path = f"/cloudsql/{instance_connection_name}"
    if os.path.exists(unix_socket_path):
        conn = pg8000.connect(
            user=db_user,
            password=db_pass,
            database=db_name,
            unix_sock=f"{unix_socket_path}/.s.PGSQL.5432"
        )
    else:
        connector = Connector()
        conn = connector.connect(
            instance_connection_name,
            "pg8000",
            user=db_user,
            password=db_pass,
            db=db_name,
            ip_type="public"
        )
    return conn

print("Creating engine...")
engine = create_engine("postgresql+pg8000://", creator=getconn)

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
