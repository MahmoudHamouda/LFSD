from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
import logging

# Initialize logger
logger = logging.getLogger("db_connection")

# Global variables for engine and session
engine = None
Session = None


def init_db_connection(config):
    """
    Initialize the shared database connection.
    :param config: Application configuration containing DB connection details.
    """
    global engine, Session

    try:
        # Create the database engine
        engine = create_engine(
            f"postgresql://{config['DB_USER']}:{config['DB_PASSWORD']}@{config['DB_HOST']}:{config['DB_PORT']}/{config['DB_NAME']}",
            pool_size=20,  # Connection pooling
            max_overflow=10,  # Allow some overflow connections
        )
        logger.info("Database engine initialized successfully.")

        # Create the session factory
        Session = sessionmaker(bind=engine)
    except SQLAlchemyError as e:
        logger.error(f"Error initializing database connection: {e}")
        raise e


def get_db_session():
    """
    Provides a database session.
    :return: A new database session.
    """
    if Session is None:
        raise RuntimeError(
            "Database connection not initialized. Call init_db_connection first."
        )
    return Session()


def initialize_schema(base):
    """
    Initialize the database schema based on the provided models.
    :param base: Declarative base containing the models.
    """
    global engine

    if engine is None:
        raise RuntimeError(
            "Database connection not initialized. Call init_db_connection first."
        )

    try:
        base.metadata.create_all(engine)
        logger.info("Database schema initialized successfully.")
    except SQLAlchemyError as e:
        logger.error(f"Error initializing database schema: {e}")

        

def get_db_connection():
    """
    Compatibility wrapper for existing cursor-based code.
    Uses psycopg2 if DATABASE_URL is set, otherwise falls back to sqlite3.
    """
    import os
    dsn = os.getenv("DATABASE_URL")
    if dsn:
        import psycopg2
        return psycopg2.connect(dsn)
    else:
        import sqlite3
        path = os.getenv("SQLITE_PATH", "dev.db")
        conn = sqlite3.connect(path, check_same_thread=False)
        return conn
raise e
