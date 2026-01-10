"""
Database connection and session management.

This module provides SQLAlchemy engine and session management for the application.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from core.config import get_settings

settings = get_settings()

# --- CLOUD SQL CONFIGURATION ---
from google.cloud.sql.connector import Connector
import pg8000

def getconn():
    connector = Connector()
    conn = connector.connect(
        "newprojectlfsd:us-central1:lfsd-postgres-prod",
        "pg8000",
        user="postgres",
        password="LfsdSecure2024!",
        db="lfsd",
        ip_type="public"
    )
    return conn

if settings.ENV == "prod":
    # Create SQLAlchemy engine with Cloud SQL Connector
    engine = create_engine(
        "postgresql+pg8000://",
        creator=getconn,
        echo=settings.DEBUG,
    )
else:
    # Use local SQLite for development
    sqlite_url = "sqlite:///backend/lfsd.db"
    print(f"DEBUG: Using local SQLite database at {sqlite_url}")
    engine = create_engine(
        sqlite_url,
        connect_args={"check_same_thread": False},
        echo=settings.DEBUG,
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()


def get_db():
    """
    Dependency function to get a database session.
    
    Usage in FastAPI routes:
        @router.get("/items")
        async def get_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize the database by creating all tables."""
    # Import models to register them with Base
    from . import models  # noqa: F401
    from . import lifestyle_events  # noqa: F401
    from . import nutrition_logs  # noqa: F401
    from . import investment_portfolios  # noqa: F401
    Base.metadata.create_all(bind=engine)
