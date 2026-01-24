from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import URL
from contextlib import contextmanager
from .models import Base
import logging

logger = logging.getLogger(__name__)

engine = None
Session = None

def init_db(app):
    """
    Initializes the database connection using the app's configuration and hardens the setup.
    """
    global engine, Session
    try:
        # 1. Secure URL Construction (Handles special characters in passwords)
        db_url = URL.create(
            drivername="postgresql+psycopg2",
            username=app.config.get("DB_USER"),
            password=app.config.get("DB_PASSWORD"),
            host=app.config.get("DB_HOST", "localhost"),
            port=app.config.get("DB_PORT", 5432),
            database=app.config.get("DB_NAME"),
        )

        # 2. Connection Hardening (pool_pre_ping for Postgres stability)
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=1800,
            echo=app.config.get("DEBUG", False)
        )

        # 3. Thread-Safe Scoped Sessions for Flask
        Session = scoped_session(
            sessionmaker(bind=engine, autocommit=False, autoflush=False)
        )

        # 4. Guarded Schema Creation (Dev only)
        if app.config.get("ENV") == "development":
            Base.metadata.create_all(engine)

        # 5. Automatic Teardown Cleanup
        @app.teardown_appcontext
        def shutdown_session(exception=None):
            if Session:
                Session.remove()

    except SQLAlchemyError as e:
        logger.error(f"Database Initialization Failed: {e}")
        raise RuntimeError(f"Failed to initialize the database: {e}")

def get_db_session():
    """Provides the raw session object."""
    if not Session:
        raise RuntimeError("Database session is not initialized. Call init_db() first.")
    return Session()

@contextmanager
def db_session():
    """
    Context manager for safe database operations.
    Handles commit on success, rollback on failure, and cleanup automatically.
    """
    session = get_db_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
