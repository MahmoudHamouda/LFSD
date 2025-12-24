import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database import init_db
import models.models # Register models

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Database initialized.")
