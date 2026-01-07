import os
import sqlalchemy
from google.cloud.sql.connector import Connector


# DB Config
INSTANCE_CONNECTION_NAME = "newprojectlfsd:us-central1:lfsd-postgres-prod"
DB_USER = "postgres"
DB_PASS = "LfsdSecure2024!"
DB_NAME = "lfsd"

def getconn():
    connector = Connector()
    conn = connector.connect(
        INSTANCE_CONNECTION_NAME,
        "pg8000",
        user=DB_USER,
        password=DB_PASS,
        db=DB_NAME,
        ip_type="public"
    )
    return conn

def check_schema():
    pool = sqlalchemy.create_engine(
        "postgresql+pg8000://",
        creator=getconn,
    )
    
    with pool.connect() as db_conn:
        result = db_conn.execute(sqlalchemy.text(
            "SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'users';"
        ))
        print("COLUMNS IN USERS TABLE:")
        found_auth0 = False
        for row in result:
            print(f"- {row[0]} ({row[1]})")
            if row[0] == 'auth0_id':
                found_auth0 = True
        
        if found_auth0:
            print("\nSUCCESS: auth0_id column EXISTS.")
        else:
            print("\nFAILURE: auth0_id column MISSING!")

if __name__ == "__main__":
    check_schema()
