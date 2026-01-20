import requests
import os
import sys

URL = "https://lfsd-backend-692544481281.us-central1.run.app/api/debug/seed_force?secret=lfsd_backup_2024"

def seed_force():
    print(f"Targeting: {URL}")
    try:
        resp = requests.post(URL)
        resp.raise_for_status()
        print("Seed Result:", resp.json())
    except Exception as e:
        print(f"Seed Failed: {e}")
        if 'resp' in locals():
            print(resp.text)
        sys.exit(1)

if __name__ == "__main__":
    seed_force()
