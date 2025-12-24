import sys
import logging
from loguru import logger
from core.config import get_settings
from models.database import SessionLocal
from models.logging_models import SystemLog
import sys


class DatabaseSink:
    """
    Loguru sink that writes logs to the SystemLog table.
    """
    def write(self, message):
        record = message.record
        
        # Avoid recursion if logging from within DB operations
        if record["name"].startswith("sqlalchemy"):
            return

        session = SessionLocal()
        try:
            log_entry = SystemLog(
                level=record["level"].name,
                message=record["message"],
                module=record["name"],
                function_name=record["function"],
                line_number=record["line"],
                timestamp=record["time"],
                extra_data=record["extra"]
            )
            session.add(log_entry)
            session.commit()
        except Exception as e:
            # Fallback to stderr if DB fails to avoid crash/loops
            # We don't log here to avoid infinite recursion
            pass
        finally:
            session.close()

class InterceptHandler(logging.Handler):
    """
    Default handler from examples in loguru documentation.
    Intercepts standard logging messages and routes them to Loguru.
    """
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

def setup_logging():
    """Configure logging for the application."""
    settings = get_settings()
    
    # Remove all existing handlers
    logging.root.handlers = []

    # Intercept everything at the root logger
    logging.basicConfig(handlers=[InterceptHandler()], level=0)

    # Remove standard uvicorn loggers to avoid duplication
    for log_name in ["uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"]:
        logging_logger = logging.getLogger(log_name)
        logging_logger.handlers = [InterceptHandler()]

    # Configure Loguru
    logger.configure(
        handlers=[
            {
                "sink": sys.stdout, 
                "level": "DEBUG" if settings.DEBUG else "INFO",
                "format": "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level> | {extra}"
            },
            {
                "sink": "app.log",
                "rotation": "500 MB",
                "retention": "10 days",
                "level": "INFO",
                "serialize": True
            },
            {
                "sink": DatabaseSink(),
                "level": "WARNING", # Only log WARNING and above to DB to prevent noise
                "enqueue": True # Run in background thread to avoid blocking
            }
        ]
    )
