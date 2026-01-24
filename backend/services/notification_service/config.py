import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "notification_secret")
    DB_USER = os.environ.get("DB_USER", "postgres")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "5432")
    DB_NAME = os.environ.get("DB_NAME", "viv_notifications")
    ENV = os.environ.get("ENV", "production")
    DEBUG = False

class DevelopmentConfig(Config):
    DEBUG = True
    ENV = "development"

def get_config():
    env = os.environ.get("ENV", "development")
    if env == "production":
        from .app import Config as ProdConfig # In case we want to separate further
        return Config()
    return DevelopmentConfig()
