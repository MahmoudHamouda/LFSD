"""
Application configuration using Pydantic's BaseSettings.

This module defines a Settings class inheriting from Pydantic's BaseSettings to
provide strongly‑typed environment configuration. Values are loaded from
environment variables and can be optionally overridden by a `.env` file. See
`README.md` for the list of supported environment variables.
"""

from functools import lru_cache
from pathlib import Path
import os

# Pydantic v2 uses `pydantic_settings` for BaseSettings. Fallback to older import if needed.
try:
    from pydantic_settings import BaseSettings  # type: ignore
    from pydantic import Field  # type: ignore
except Exception:
    try:
        from pydantic import BaseSettings, Field  # type: ignore
    except Exception:
        # Minimal fallback implementations if Pydantic is unavailable.
        class BaseSettings:
            """Fallback BaseSettings that simply stores provided values."""
            def __init__(self, **values):
                for k, v in values.items():
                    setattr(self, k, v)

        def Field(default, description: str = "", **kwargs):  # noqa: D401
            return default

class Settings(BaseSettings):
    """Configuration for the LFSD application."""

    APP_NAME: str = Field("lfsd", description="Human readable name of the application")
    ENV: str = Field(os.environ.get("ENV", "dev"), description="Environment name, e.g. dev/staging/prod")
    DEBUG: bool = Field(str(os.environ.get("DEBUG", "false")).lower() == "true", description="Enable debug mode")
    SECRET_KEY: str = Field(os.environ.get("SECRET_KEY", "fallback-dev-secret-key"), description="Secret key for JWT signing")
    
    JWT_ALG: str = Field("HS256", description="Algorithm used to sign JWT tokens")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(60, description="Access token expiry window in minutes")
    ALLOWED_ORIGINS: str = Field("*", description="Comma separated list of allowed CORS origins. Use '*' for any origin.")
    RATE_LIMIT: str = Field("100/minute", description="Default request rate limit in 'N/period' format.")
    REDIS_URL: str = Field("redis://redis:6379/0", description="Redis connection URL for rate limiting and caching")
    DATABASE_URL: str = Field("sqlite:///./lfsd_v2.db", description="Database connection URL (SQLite for dev, PostgreSQL for prod)")
    UBER_SERVER_TOKEN: str = Field("", description="Uber API Server Token for price estimates and ride requests")
    GEMINI_API_KEY: str = Field("AIzaSyDwhejk-FKUDtA47i5qH4HHGFJEDaX2KBw", env="GEMINI_API_KEY", description="Google Gemini API Key for chat generation")
    GEMINI_MODEL: str = Field("gemini-2.0-flash-exp", description="Optional explicit Gemini model name (overrides auto‑detect)")
    
    # Careem Integration
    CAREEM_API_KEY: str = Field("", description="Careem API Key for booking and estimates")
    CAREEM_API_SECRET: str = Field("", description="Careem API Secret for authentication")

    # Bolt Integration
    BOLT_API_KEY: str = Field("", description="Bolt API Key for booking and estimates")

    # RTA Integration
    RTA_API_KEY: str = Field("", description="RTA API Key for public transit data")

    # Google Maps Integration
    GOOGLE_MAPS_API_KEY: str = Field("", description="Google Maps API Key for geocoding and distance matrix")

    # Google Calendar Integration
    GOOGLE_CLIENT_ID: str = Field("", description="Google OAuth Client ID")
    GOOGLE_CLIENT_SECRET: str = Field("", description="Google OAuth Client Secret")

    # Microsoft Graph Integration
    MICROSOFT_CLIENT_ID: str = Field("", description="Microsoft Graph Client ID")
    MICROSOFT_CLIENT_SECRET: str = Field("", description="Microsoft Graph Client Secret")
    MICROSOFT_TENANT_ID: str = Field("common", description="Microsoft Tenant ID (common for multi-tenant)")

    # Skyscanner Integration
    RAPIDAPI_KEY: str = Field("", description="RapidAPI Key for Skyscanner")
    SKYSCANNER_API_KEY: str = Field("", description="Skyscanner API Key (if direct)")

    # Booking.com Integration
    BOOKING_API_KEY: str = Field("", description="Booking.com API Key")
    BOOKING_AFFILIATE_ID: str = Field("", description="Booking.com Affiliate ID")

    # Email / SMTP Configuration
    SMTP_SERVER: str = Field("", description="SMTP Server Host (e.g., smtp.gmail.com)")
    SMTP_PORT: int = Field(587, description="SMTP Server Port (e.g., 587 for TLS)")
    SMTP_USERNAME: str = Field("", description="SMTP Username")
    SMTP_PASSWORD: str = Field("", description="SMTP Password")
    EMAILS_FROM_EMAIL: str = Field("", description="Email address to send from")
    EMAILS_FROM_NAME: str = Field("Viv App", description="Name to display as sender")

    # Pydantic v2 uses `model_config` for settings.
    model_config = {
        "env_file": str(Path(__file__).resolve().parent.parent.parent / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "allow",
    }

@lru_cache()
def get_settings() -> Settings:
    """Return a cached instance of Settings."""
    settings = Settings()
    if settings.SECRET_KEY == "change_me" and not settings.DEBUG:
        raise ValueError("Critical Security Violation: SECRET_KEY is set to 'change_me' in a non-debug environment. Update .env with a secure key.")
    return settings