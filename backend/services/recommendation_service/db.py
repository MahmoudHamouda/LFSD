from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import URL
from contextlib import contextmanager
import logging
import os

from .models import Base

logger = logging.getLogger(__name__)

# Global state for engine and session factory
_engine = None
_SessionFactory = None

def init_db(app):
    """
    Initializes the database engine and scoped session factory.
    Registers a teardown handler to ensure sessions are removed.
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
        # Added pool sizing and overflow for production scaling
        _engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=1800,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            # Use echo=False in prod; only enable selectively
            echo=False, 
            future=True # SQLAlchemy 2.0 style
        )

        # 3. Thread-Safe Scoped Sessions
        _SessionFactory = scoped_session(
            sessionmaker(bind=_engine, autocommit=False, autoflush=False)
        )

        # 4. Robust Schema Guard
        # Check multiple possible environment keys
        env = app.config.get("ENV") or os.environ.get("FLASK_ENV") or "production"
        if env.lower() in ["development", "dev", "test", "testing"]:
            logger.info(f"Automatically creating schema for {env} environment.")
            Base.metadata.create_all(_engine)

        # 5. Safe Teardown Registration
        # This handles the cleanup of scoped sessions per request
        if not hasattr(app, '_db_teardown_registered'):
            @app.teardown_appcontext
            def shutdown_session(exception=None):
                if _SessionFactory:
                    _SessionFactory.remove()
            app._db_teardown_registered = True

    except Exception as e:
        logger.error(f"Critical Database Initialization Failure: {e}", exc_info=True)
        raise RuntimeError(f"Could not initialize database: {e}")

def get_db_session():
    """Returns the scoped session instance (registry)."""
    if not _SessionFactory:
        raise RuntimeError("Database session factory is not initialized. Call init_db() first.")
    return _SessionFactory

@contextmanager
def db_session(auto_commit: bool = True):
    """
    Context manager for safe database operations.
    - auto_commit: If True (default), commits on exit if no exception occurred.
    - Correctly uses .remove() via the thread-local registry logic.
    """
    session = get_db_session()
    try:
        yield session
        if auto_commit:
            session.commit()
    except Exception:
        session.rollback()
        raise # Maintain traceback context
    # Note: Scoped session removal is handled primarily by app teardown.
    # Individual .close() can be called here but .remove() is cleaner for the registry.
    finally:
        session.close() # Return connection to pool; teardown handles registry removal
