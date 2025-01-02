import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    TESTING = os.getenv("TESTING", "False").lower() in ("true", "1", "t")
    SECRET_KEY = os.getenv("SECRET_KEY", "default-secret-key")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Construct database URI from individual components or fallback to DATABASE_URL
    @staticmethod
    def construct_db_uri():
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME")

        if db_user and db_password and db_name:
            return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        return os.getenv("DATABASE_URL", "sqlite:///default.db")

    SQLALCHEMY_DATABASE_URI = construct_db_uri()

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = Config.construct_db_uri()

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = Config.construct_db_uri()

def get_config():
    config_map = {
        "production": ProductionConfig,
        "testing": TestingConfig,
        "development": DevelopmentConfig,
    }
    env = os.getenv("FLASK_ENV", "development").lower()
    return config_map.get(env, DevelopmentConfig)
