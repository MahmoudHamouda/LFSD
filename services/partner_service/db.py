from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

engine = None

def init_db(app):
    global engine
    engine = create_engine(f"postgresql://{app.config['DB_USER']}:{app.config['DB_PASSWORD']}@{app.config['DB_HOST']}:{app.config['DB_PORT']}/{app.config['DB_NAME']}")
    Base.metadata.create_all(engine)

def get_db_session():
    global engine
    Session = sessionmaker(bind=engine)
    return Session()
