import sys
import os

# Add parent directory to path to allow importing modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.database import init_db, engine
# Import models to register them with SQLAlchemy
import models.models 

print("Initializing database...")
init_db()
print("Database initialized.")
