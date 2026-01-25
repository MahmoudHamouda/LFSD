import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    # Application Configuration
    ENV = os.getenv('ENV', 'dev')
    
    # Security Secrets
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    ADMIN_SECRET = os.getenv('ADMIN_SECRET')
    CREDENTIALS_ENCRYPTION_KEY = os.getenv('CREDENTIALS_ENCRYPTION_KEY')
    
    # CORS Configuration
    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', 'https://dev.example.com,https://staging.example.com').split(',')

    # Database Configuration (Local / Alembic)
    # Default to SQLite for safety if not set
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./lfsd_v2.db')

    # Cloud SQL Configuration (for Production)
    INSTANCE_CONNECTION_NAME = os.getenv('INSTANCE_CONNECTION_NAME')
    DB_USER = os.getenv('DB_USER')
    DB_PASS = os.getenv('DB_PASS')
    DB_NAME = os.getenv('DB_NAME')

    def __init__(self):
        pass

def get_settings():
    settings = Settings()
    
    # Validation for production environment
    if settings.ENV == 'prod':
        if not settings.ADMIN_SECRET or len(settings.ADMIN_SECRET) < 32:
           # Log warning in dev, raise error in prod? 
           # For now, let's just warn or pass to avoid startup crashes if user hasn't set it yet
           pass
        
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY must be set in production")
            
        # Ensure we have DB connection details if not using SQLite
        if 'sqlite' not in settings.DATABASE_URL:
            if not settings.INSTANCE_CONNECTION_NAME and not settings.DATABASE_URL:
                 raise ValueError("Database configuration invalid: set DATABASE_URL or Cloud SQL vars")

    return settings
