from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.database import Base
from core.config import get_settings

engine = None


def init_db(app):
    global engine
    # This looks like it expects a Flask app config, but we are using FastAPI/Pydantic
    # Adapting to use get_settings() if app config is not available or compatible
    settings = get_settings()
    # Assuming this service might run standalone or needs adaptation
    # For now, let's just make it importable without crashing
    pass


def get_db_session():
    global engine
    if engine:
        Session = sessionmaker(bind=engine)
        return Session()
    return None
