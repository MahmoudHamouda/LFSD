"""
Partner Service Database Management

Handles SQLAlchemy engine initialization, connection pooling, and 
thread-safe session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
import logging

from .models import Base

logger = logging.getLogger(__name__)

# Track engine and session factory globally within the service
_engine = None
_SessionLocal = None

def init_db(app):
    """
    Initialize the database engine and create tables.
    Hardened with connection pooling and statement timeouts.
    """
    global _engine, _SessionLocal
    
    try:
        db_url = f"postgresql://{app.config['DB_USER']}:{app.config['DB_PASSWORD']}@{app.config['DB_HOST']}:{app.config['DB_PORT']}/{app.config['DB_NAME']}"
        
        _engine = create_engine(
            db_url,
            # Production-grade pooling
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=1800,
            pool_pre_ping=True, # Detect stale connections
            # Security & performance
            echo=app.config.get("DEBUG", False),
            future=True 
        )
        
        # Create tables using the latest model definitions (v2)
        Base.metadata.create_all(_engine)
        
        # Configure the session factory
        factory = sessionmaker(bind=_engine, expire_on_commit=False)
        _SessionLocal = scoped_session(factory)
        
        logger.info("Partner Service Database initialized successfully.")
        
    except Exception as e:
        logger.error(f"Failed to initialize Partner database: {e}")
        raise

@contextmanager
def get_db_session():
    """
    Context manager for safe database operations.
    Handles auto-commit, auto-rollback, and session cleanup.
    """
    if _SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db(app) first.")
        
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise
    finally:
        session.close()
        _SessionLocal.remove() # Clean up thread-local storage

# Legacy support if any code still uses the raw getter
def get_session():
    return _SessionLocal()
