import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings:
    # Application Configuration
    ENV = os.getenv("ENV", "dev")
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"
    API_V1_STR = os.getenv("API_V1_STR", "/api")

    # Security Secrets
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv(
        "GEMINI_MODEL", "gemini-2.5-flash"
    )  # Updated to 2.5 Flash (2.0 deprecated March 2026)
    GEMINI_MODEL_LIGHT = os.getenv(
        "GEMINI_MODEL_LIGHT", "gemini-2.5-flash"
    )  # Tier 1-2: lightweight
    GEMINI_MODEL_HEAVY = os.getenv(
        "GEMINI_MODEL_HEAVY", "gemini-2.5-pro"
    )  # Tier 3: heavy reasoning
    ADMIN_SECRET = os.getenv("ADMIN_SECRET")
    CREDENTIALS_ENCRYPTION_KEY = os.getenv("CREDENTIALS_ENCRYPTION_KEY")

    # Uber
    UBER_CLIENT_ID = os.getenv("UBER_CLIENT_ID")
    UBER_CLIENT_SECRET = os.getenv("UBER_CLIENT_SECRET")

    # Stripe
    STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")

    # WhatsApp
    WHATSAPP_API_TOKEN = os.getenv("WHATSAPP_API_TOKEN")

    # Integration Tokens
    UBER_SERVER_TOKEN = os.getenv("UBER_SERVER_TOKEN")
    RTA_API_KEY = os.getenv("RTA_API_KEY")
    RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")
    SKYSCANNER_API_KEY = os.getenv("SKYSCANNER_API_KEY")
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

    # Base URL for Callbacks
    APP_BASE_URL = os.getenv(
        "APP_BASE_URL", "https://lfsd-backend-692544481281.us-central1.run.app"
    )

    # CORS Configuration
    ALLOWED_ORIGINS = os.getenv(
        "ALLOWED_ORIGINS", "https://dev.example.com,https://staging.example.com"
    )

    # Database Configuration (Local / Alembic)
    # Default to SQLite for safety if not set
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./lfsd_v2.db")

    # Cloud SQL Configuration (for Production)
    INSTANCE_CONNECTION_NAME = os.getenv("INSTANCE_CONNECTION_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASS = os.getenv("DB_PASS")
    DB_NAME = os.getenv("DB_NAME")

    # Security & Auth
    APP_NAME = os.getenv("APP_NAME", "LFSD")
    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_ALG = os.getenv("JWT_ALG", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    RATE_LIMIT = os.getenv("RATE_LIMIT", "100/minute")
    REDIS_URL = os.getenv("REDIS_URL")

    # Auth0
    AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")
    AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID")
    AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET")

    def __init__(self):
        pass


def get_settings():
    settings = Settings()

    # Validation for production environment
    if settings.ENV == "prod":
        if not settings.ADMIN_SECRET or len(settings.ADMIN_SECRET) < 48:
            raise ValueError(
                "ADMIN_SECRET must be at least 48 characters in production"
            )

        if not settings.SECRET_KEY or len(settings.SECRET_KEY) < 48:
            raise ValueError("SECRET_KEY must be at least 48 characters in production")

        if not settings.CREDENTIALS_ENCRYPTION_KEY:
            raise ValueError("CREDENTIALS_ENCRYPTION_KEY must be set in production")

        if not all(
            [
                settings.AUTH0_DOMAIN,
                settings.AUTH0_CLIENT_ID,
                settings.AUTH0_CLIENT_SECRET,
            ]
        ):
            raise ValueError(
                "AUTH0_DOMAIN, AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET must all be set in production"
            )

        if "sqlite" not in settings.DATABASE_URL:
            if not settings.INSTANCE_CONNECTION_NAME and not settings.DATABASE_URL:
                raise ValueError(
                    "Database configuration invalid: set DATABASE_URL or Cloud SQL vars"
                )

    return settings
