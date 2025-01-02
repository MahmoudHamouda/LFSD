from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

# Declare engine as None initially
engine = None

def init_db(app):
    """
    Initialize the database connection using the app configuration.
    """
    global engine
    try:
        engine = create_engine(
            f"postgresql://{app.config['DB_USER']}:{app.config['DB_PASSWORD']}@{app.config['DB_HOST']}:{app.config['DB_PORT']}/{app.config['DB_NAME']}"
        )
        # Create all tables defined in models.Base
        Base.metadata.create_all(engine)
    except Exception as e:
        raise RuntimeError(f"Database initialization failed: {e}")

def get_db_session():
    """
    Get a new session for interacting with the database.
    """
    global engine
    if not engine:
        raise RuntimeError("Database engine is not initialized. Call init_db first.")
    try:
        Session = sessionmaker(bind=engine)
        return Session()
    except Exception as e:
        raise RuntimeError(f"Failed to create database session: {e}")
