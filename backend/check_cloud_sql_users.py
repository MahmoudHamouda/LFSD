"""
Check users in Cloud SQL database
"""

import os
os.environ["DATABASE_URL"] = "postgresql://lfsd_user:LFSDProd2026SecurePass!@136.119.201.13:5432/lfsd"

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

engine = create_engine(os.environ["DATABASE_URL"])
Session = sessionmaker(bind=engine)
session = Session()

print("Checking users in Cloud SQL database...")
print("-" * 80)

# Query users
result = session.execute(text("SELECT id, email, hashed_password FROM users;"))
users = result.fetchall()

if not users:
    print("No users found in database!")
else:
    for user in users:
        print(f"ID: {user[0]}")
        print(f"Email: {user[1]}")
        print(f"Password Hash (first 50 chars): {user[2][:50]}...")
        print("-" * 80)

session.close()
