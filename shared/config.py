import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()


class Config:
    """
    Base configuration class with default settings.
    """

    # General Configuration
    APP_NAME = "Financial Wellbeing Platform"
    ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = ENV == "development"

    # Database Configuration
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
    DB_NAME = os.getenv("DB_NAME", "financial_app")

    # OpenAI API Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your_openai_api_key")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")

    # JWT Configuration
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your_jwt_secret_key")
    JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", 24))

    # Rate Limiting Configuration
    RATE_LIMIT_DEFAULT = int(
        os.getenv("RATE_LIMIT_DEFAULT", 100)
    )  # Requests per minute
    RATE_LIMIT_ENDPOINTS = {
        "/chat": int(os.getenv("RATE_LIMIT_CHAT", 50)),
        "/recommendations": int(os.getenv("RATE_LIMIT_RECOMMENDATIONS", 30)),
    }

    # Security Settings
    CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "*")

    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
    LOG_FILE = os.getenv("LOG_FILE", "application.log")


# Environment-specific configurations
class DevelopmentConfig(Config):
    DEBUG = True


class TestingConfig(Config):
    DEBUG = True
    TESTING = True
    DB_NAME = os.getenv("TEST_DB_NAME", "test_financial_app")


class ProductionConfig(Config):
    DEBUG = False
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


# Factory method to load appropriate configuration
def get_config():
    """
    Load the appropriate configuration based on the environment.
    """
    env = os.getenv("FLASK_ENV", "development")
    if env == "production":
        return ProductionConfig()
    elif env == "testing":
        return TestingConfig()
    return DevelopmentConfig()
