"""
Auth0 Configuration Module
Handles Auth0 authentication setup and token validation
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Auth0Settings(BaseSettings):
    """Auth0 configuration settings"""
    
    AUTH0_DOMAIN: str
    AUTH0_CLIENT_ID: str
    AUTH0_CLIENT_SECRET: str
    AUTH0_AUDIENCE: str
    AUTH0_ALGORITHMS: list = ["RS256"]
    
    class Config:
        env_file = ".env"
        extra = "ignore"


def validate_auth0_config() -> None:
    """
    Validate that required Auth0 configuration is present.
    Raises ValueError if critical Auth0 settings are missing in production.
    """
    settings = Auth0Settings()
    required_vars = ["AUTH0_DOMAIN", "AUTH0_CLIENT_ID", "AUTH0_CLIENT_SECRET"]
    missing = [var for var in required_vars if not getattr(settings, var, None)]
    
    if missing:
        raise ValueError(
            f"Missing required Auth0 environment variables: {', '.join(missing)}. "
            "Please set these in your .env file or environment."
        )

@lru_cache()
def get_auth0_settings() -> Auth0Settings:
    """Get cached Auth0 settings instance"""
    return Auth0Settings()