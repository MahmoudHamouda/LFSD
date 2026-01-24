import os

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev_secret_key")
    DEBUG = False
    TESTING = False
    
    # DB Configuration
    DB_USER = os.environ.get("DB_USER", "postgres")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "postgres")
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "5432")
    DB_NAME = os.environ.get("DB_NAME", "viv_partners_db")
    
    ENV = os.environ.get("ENV", "production")

class DevelopmentConfig(Config):
    DEBUG = True
    ENV = "development"

class ProductionConfig(Config):
    DEBUG = False
    ENV = "production"

def get_config():
    env = os.environ.get("ENV", "development")
    if env == "production":
        return ProductionConfig()
    return DevelopmentConfig()
