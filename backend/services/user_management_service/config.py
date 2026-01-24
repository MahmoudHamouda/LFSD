import os

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    DB_USER = os.environ.get("DB_USER", "postgres")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "5432")
    DB_NAME = os.environ.get("DB_NAME", "users_service")
    ENV = os.environ.get("ENV", "development")
    DEBUG = os.environ.get("DEBUG", "True").lower() == "true"

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    ENV = "production"

class TestingConfig(Config):
    TESTING = True
    DB_NAME = os.environ.get("DB_NAME", "users_service_test")

def get_config():
    env = os.environ.get("ENV", "development")
    if env == "production":
        return ProductionConfig()
    if env == "testing":
        return TestingConfig()
    return DevelopmentConfig()
