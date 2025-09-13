"""
Application configuration using Pydantic's BaseSettings.

This module defines a Settings class inheriting from Pydantic's BaseSettings to
provide strongly‑typed environment configuration. Values are loaded from
environment variables and can be optionally overridden by a `.env` file. See
`README.md` for the list of supported environment variables.
"""

from functools import lru_cache
# Pydantic moved BaseSettings to pydantic-settings in v2. Attempt to import
# from the new location first, falling back to pydantic if available. If
# neither is available, provide a minimal fallback implementation so the
# application can still run in constrained environments.
try:
    from pydantic_settings import BaseSettings  # type: ignore
    from pydantic import Field  # type: ignore
except Exception:
    try:
        from pydantic import BaseSettings, Field  # type: ignore
    except Exception:
        # Define minimal fallback implementations for BaseSettings and Field.
        class BaseSettings:
            """
            A minimal stand-in for pydantic BaseSettings used when pydantic is
            unavailable. It simply stores attributes from keyword arguments and
            ignores environment variable loading.
            """

            def __init__(self, **values) -> None:  # type: ignore[override]
                for key, value in values.items():
                    setattr(self, key, value)

            class Config:
                env_file = None
                env_file_encoding = "utf-8"
                case_sensitive = False

        def Field(default, description: str = "", **kwargs):  # type: ignore[override]
            # In fallback mode, Field simply returns the default value. Additional
            # metadata such as description is ignored.
            return default

        # Import Any for type annotations in fallback mode
        from typing import Any  # noqa: E401  # placed here to satisfy mypy


class Settings(BaseSettings):
    """Configuration for the LFSD application."""

    APP_NAME: str = Field("lfsd", description="Human readable name of the application")
    ENV: str = Field("dev", description="Environment name, e.g. dev/staging/prod")
    DEBUG: bool = Field(True, description="Enable debug mode")
    SECRET_KEY: str = Field("change_me", description="Secret key for JWT signing")
    JWT_ALG: str = Field("HS256", description="Algorithm used to sign JWT tokens")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        60, description="Access token expiry window in minutes"
    )
    ALLOWED_ORIGINS: str = Field(
        "*",
        description=(
            "Comma separated list of allowed CORS origins. Use '*' for any origin."
        ),
    )
    RATE_LIMIT: str = Field(
        "100/minute",
        description=(
            "Default request rate limit in 'N/period' format. See slowapi docs."
        ),
    )
    REDIS_URL: str = Field(
        "redis://redis:6379/0",
        description="Redis connection URL for rate limiting and caching",
    )

    class Config:
        """Custom configuration for Pydantic settings."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Return a cached instance of Settings."""
    return Settings()