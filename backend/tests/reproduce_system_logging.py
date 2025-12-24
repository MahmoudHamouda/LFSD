
import sys
import os
import time
import logging

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from models.logging_models import SystemLog, Base
import models.database # Import module to patch it

SQLITE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLITE_URL, 
    connect_args={"check_same_thread": False}, 
    poolclass=StaticPool
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

# Import logging config and PATCH it directly
import core.logging_config
core.logging_config.SessionLocal = TestSessionLocal
from core.logging_config import setup_logging
from loguru import logger

def verify_system_logging():
    print("Setting up logging...")
    setup_logging()
    
    # Trigger a log
    print("Triggering log message...")
    logger.warning("This is a TEST warning for DB persistence.")
    
    # Wait for async sink (enqueue=True)
    time.sleep(1)
    
    # Verify
    db = TestSessionLocal()
    try:
        log_entry = db.query(SystemLog).filter(SystemLog.message.contains("TEST warning")).first()
        if log_entry:
            print(f"SUCCESS: Log found in DB. ID: {log_entry.id}, Level: {log_entry.level}, Msg: {log_entry.message}")
            print("SUCCESS_LOGGING")
        else:
            print("FAILURE: Log NOT found in DB.")
            # Debug: print all logs
            logs = db.query(SystemLog).all()
            print(f"Found {len(logs)} logs in DB:")
            for l in logs:
                print(f" - {l.level}: {l.message}")
    finally:
        db.close()

if __name__ == "__main__":
    verify_system_logging()
