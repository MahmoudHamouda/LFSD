"""
Auth0 Configuration Module
Handles Auth0 authentication setup and token validation
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Auth0Settings(BaseSettings):
    """Auth0 configuration settings"""
    
    AUTH0_DOMAIN: str = "dev-lmc05ou12e7ep05p.eu.auth0.com"
    AUTH0_CLIENT_ID: str = "VVw94DZQITVcARsNlp4JEZkyzMjsgioF"
    AUTH0_CLIENT_SECRET: str = "vfMd6SgVMU3HYeQvFvjU4Au0i2mbpHYR_lepVuDYvdepslGRyQR1AS235hsqcHMj"
    AUTH0_AUDIENCE: str = f"https://dev-lmc05ou12e7ep05p.eu.auth0.com/api/v2/"
    AUTH0_ALGORITHMS: list = ["RS256"]
    
    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_auth0_settings() -> Auth0Settings:
    """Get cached Auth0 settings instance"""
    return Auth0Settings()
