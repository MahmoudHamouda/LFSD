import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

class Config:
    # General Configuration
    APP_NAME = "API Gateway"
    ENV = os.getenv("FLASK_ENV", "development")
    DEBUG = ENV == "development"

    # Database Configuration
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
    DB_NAME = os.getenv("DB_NAME", "financial_app")

    # JWT Configuration
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your_secret_key")
    JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", 1))

    # Rate Limiting Configuration
    RATE_LIMIT_DEFAULT = int(os.getenv("RATE_LIMIT_DEFAULT", 100))  # Requests per minute
    RATE_LIMIT_ENDPOINTS = {
        "/users/<int:user_id>/chat": int(os.getenv("RATE_LIMIT_CHAT", 50)),
        "/recommendations": int(os.getenv("RATE_LIMIT_RECOMMENDATIONS", 30)),
    }

    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
    LOG_FILE = os.getenv("LOG_FILE", "api_gateway.log")

    # OpenAI API Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your_openai_api_key")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")

    # Third-Party Service Configuration
    THIRD_PARTY_SERVICES = {
        "uber": {
            "api_key": os.getenv("UBER_API_KEY", ""),
            "api_endpoint": os.getenv("UBER_API_ENDPOINT", "https://api.uber.com/v1"),
        },
        "opentable": {
            "api_key": os.getenv("OPENTABLE_API_KEY", ""),
            "api_endpoint": os.getenv("OPENTABLE_API_ENDPOINT", "https://api.opentable.com/v1"),
        },
    }

    # Security Settings
    CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "*")


# Factory method to get environment-specific configuration
def get_config():
    env = os.getenv("FLASK_ENV", "development")
    if env == "production":
        return ProductionConfig()
    elif env == "testing":
        return TestingConfig()
    return Config()


# Environment-Specific Configurations
class ProductionConfig(Config):
    DEBUG = False
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


class TestingConfig(Config):
    DEBUG = True
    TESTING = True
    DB_NAME = os.getenv("TEST_DB_NAME", "test_financial_app")
