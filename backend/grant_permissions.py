import pg8000
from google.cloud.sql.connector import Connector
import sqlalchemy

def grant_access():
    instance_connection_name = "newprojectlfsd:us-central1:lfsd-postgres-prod"
    db_user = "postgres"
    db_pass = "LfsdSecure2024!"
    db_name = "lfsd"

    connector = Connector()

    def getconn():
        conn = connector.connect(
            instance_connection_name,
            "pg8000",
            user=db_user,
            password=db_pass,
            db=db_name,
            ip_type="public"
        )
        return conn

    pool = sqlalchemy.create_engine(
        "postgresql+pg8000://",
        creator=getconn,
    )

    with pool.connect() as db_conn:
        # Transaction is auto-begun
        db_conn.execute(sqlalchemy.text("GRANT ALL PRIVILEGES ON DATABASE lfsd TO lfsd_app;"))
        db_conn.execute(sqlalchemy.text("GRANT ALL ON SCHEMA public TO lfsd_app;"))
        db_conn.commit()
    
    print("Permissions granted.")

if __name__ == "__main__":
    grant_access()
