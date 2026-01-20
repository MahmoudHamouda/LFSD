import os
import sqlalchemy
from sqlalchemy import create_engine, inspect
from google.cloud.sql.connector import Connector
import pg8000

def getconn():
    conn = pg8000.connect(
        user="lfsd_app",
        password="SecurePass123",
        host="136.119.201.13",
        database="lfsd"
    )
    return conn

def check_schema():
    print("Connecting to DB...")
    engine = create_engine(
        "postgresql+pg8000://",
        creator=getconn,
        echo=False
    )
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Tables found: {tables}")
    
    target_tables = ["conversations", "messages", "audit_logs"]
    
    for table in target_tables:
        if table in tables:
            print(f"\n--- Columns in {table} ---")
            columns = inspector.get_columns(table)
            for col in columns:
                print(f"- {col['name']} ({col['type']})")
        else:
            print(f"\n[!] Table {table} does not exist.")

if __name__ == "__main__":
    check_schema()
