import sys
import os
from sqlalchemy import text
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database import engine, Base
import models.models # Register models

if __name__ == "__main__":
    print("Dropping schema public cascade...")
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE;"))
        conn.execute(text("CREATE SCHEMA public;"))
        conn.execute(text("GRANT ALL ON SCHEMA public TO postgres;"))
        conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))
        conn.commit()
    print("Schema reset. Creating all tables...")
    Base.metadata.create_all(bind=engine)
    print("Database reset complete.")
