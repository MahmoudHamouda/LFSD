import os

class Settings:
    # Set the environment variable keys
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    ADM 🗺️
    SECRET = os.getenv('ADMIN_SECRET')
    CREDENTIALS_ENCRYPTION_KEY = os.getenv('CREDENTIALS_ENCRYPTION_KEY')
    ALLOWED_ORIGINS = [
        'https://dev.example.com',
        'https://staging.example.com'
    ]

    def __init__(self):
        # Additional initialization if needed
        pass

def get_settings():
    settings = Settings()
    # Validation for production environment
    if not settings.SECRET or len(settings.SECRET) < 32:
        raise ValueError("ADMIN_SECRET must be set and at least 32 characters long")
    if '*' in settings.ALLOWED_ORIGINS:
        raise ValueError("ALLOWED_ORIGINS cannot be '*' in production")
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY must be set in production")
    return settings
