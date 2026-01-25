import traceback
import sys
import os

# Ensure backend dir is in path
sys.path.insert(0, os.getcwd())

try:
    with open('traceback.log', 'w') as f:
        try:
            print("Starting import...")
            from app import app
            f.write("Import Success!")
        except:
            traceback.print_exc(file=f)
except Exception as e:
    print(e)
