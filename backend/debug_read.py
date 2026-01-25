import os
path = "services/productivity/google_calendar_service.py"
print(f"Reading {path}")
try:
    with open(path, "r") as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            if 160 <= i+1 <= 170:
                print(f"{i+1}: {line}", end='')
except Exception as e:
    print(f"Error: {e}")
