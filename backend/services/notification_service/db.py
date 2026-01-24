"""
Notification Service Database Management
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.engine import URL
from contextlib import contextmanager
import logging

from models import Base

logger = logging.getLogger(__name__)

# Global instances (effectively singletons for the service lifecycle)
_engine = None
_SessionFactory = None

def init_db(app):
    """
    Initializes the database engine and scoped session factory.
    Hardened with connection pooling, recycling, and secure URL creation.
    """
    global _engine, _SessionFactory
    
    if _engine is not None:
        return # Already initialized

    try:
        # 1. Secure URL Construction
        db_url = URL.create(
            drivername="postgresql+psycopg2",
            username=app.config.get("DB_USER"),
            password=app.config.get("DB_PASSWORD"),
            host=app.config.get("DB_HOST", "localhost"),
            port=app.config.get("DB_PORT", 5432),
            database=app.config.get("DB_NAME"),
        )
        
        # 2. Hardened Engine Configuration
        _engine = create_engine(
            db_url,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,      # Default 30s
            pool_recycle=1800,    # Recycle connections after 30 mins
            pool_pre_ping=True,   # Heartbeat to detect stale connections
            echo=app.config.get("DEBUG", False),
            future=True
        )
        
        # 3. Guarded Schema Creation (Development only)
        if app.config.get("ENV") == "development":
            Base.metadata.create_all(_engine)
            logger.info("Database schema created/verified.")
        
        # 4. Thread-Safe Scoped Sessions
        _SessionFactory = scoped_session(
            sessionmaker(bind=_engine, autocommit=False, autoflush=False)
        )

        # 5. Flask Teardown Hook
        @app.teardown_appcontext
        def shutdown_session(exception=None):
            if _SessionFactory:
                _SessionFactory.remove()
                
        logger.info("Notification Database successfully initialized.")

    except Exception as e:
        logger.error(f"CRITICAL: Notification DB Initialization failed: {e}")
        # Reset globals to allow retry or prevent partial state usage
        _engine = None
        _SessionFactory = None
        raise

@contextmanager
def get_db_session():
    """
    Context manager for safe database operations.
    Handles rollback on ANY exception and commits on success.
    Usage: with get_db_session() as session: ...
    """
    if _SessionFactory is None:
        raise RuntimeError("Database not initialized. Ensure init_db(app) was called.")
        
    session = _SessionFactory()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Transaction rollback due to exception: {e}")
        raise
    finally:
        # scoped_session.remove() is handled by app teardown, 
        # but we explicitly close the individual session here.
        session.close()

# For callers who need a raw session without a context manager (use with caution)
def get_session():
    if _SessionFactory is None:
        raise RuntimeError("Database not initialized")
    return _SessionFactory()
