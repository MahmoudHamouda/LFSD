from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base  # Use relative import for models

# Define engine globally but do not initialize it yet
engine = None

def init_db(app):
    """
    Initialize the database engine and create all tables.
    """
    global engine
    # Create the engine using configuration from the Flask app
    engine = create_engine(
        f"postgresql://{app.config['DB_USER']}:{app.config['DB_PASSWORD']}@"
        f"{app.config['DB_HOST']}:{app.config['DB_PORT']}/{app.config['DB_NAME']}"
    )
    # Create all tables defined in the Base metadata
    Base.metadata.create_all(engine)

def get_db_session():
    """
    Create and return a new database session.
    """
    global engine
    if engine is None:
        raise RuntimeError("Database engine is not initialized. Call init_db first.")
    Session = sessionmaker(bind=engine)
    return Session()
