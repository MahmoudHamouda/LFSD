import sys
import os

# Mimic the import path environment if needed
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    print("Attempting to import models...")
    from backend.models import User
    print("User model imported successfully.")
    
    from backend.models import Order
    print("Order model imported successfully.")
    
    # Trigger mapper configuration
    from sqlalchemy.orm import configure_mappers
    configure_mappers()
    print("Mappers configured successfully.")
except Exception as e:
    print(f"CRASHED: {e}")
    import traceback
    traceback.print_exc()
