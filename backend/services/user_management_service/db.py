from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from models import Base

engine = None
Session = None

def init_db(app):
    """
    Initializes the database connection using the app's configuration.
    """
    global engine, Session
    try:
        # Create the database engine
        engine = create_engine(
            f"postgresql://{app.config['DB_USER']}:{app.config['DB_PASSWORD']}@{app.config['DB_HOST']}:{app.config['DB_PORT']}/{app.config['DB_NAME']}"
        )
        # Bind the engine to the sessionmaker
        Session = sessionmaker(bind=engine)
        # Create tables if they do not exist
        Base.metadata.create_all(engine)
    except SQLAlchemyError as e:
        raise RuntimeError(f"Failed to initialize the database: {e}")

def get_db_session():
    """
    Provides a new database session.
    """
    if not Session:
        raise RuntimeError("Database session is not initialized. Call init_db() first.")
    try:
        return Session()
    except SQLAlchemyError as e:
        raise RuntimeError(f"Failed to create a database session: {e}")
