"""
Fix the password for finance@helm.com to match backend's hashing method
"""

import os
os.environ["DATABASE_URL"] = "postgresql://lfsd_user:LFSDProd2026SecurePass!@136.119.201.13:5432/lfsd"

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import bcrypt

engine = create_engine(os.environ["DATABASE_URL"])
Session = sessionmaker(bind=engine)
session = Session()

print("Fixing password for finance@helm.com...")

# Generate new password hash using bcrypt directly (matching backend)
password = "password123"
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

print(f"New hash (first 30 chars): {hashed[:30]}...")

# Update the user
result = session.execute(
    text("UPDATE users SET hashed_password = :hash WHERE email = :email"),
    {"hash": hashed, "email": "finance@helm.com"}
)
session.commit()

print(f"✓ Updated {result.rowcount} user(s)")
print("✓ Password reset to: password123")

# Verify
result = session.execute(
    text("SELECT email, hashed_password FROM users WHERE email = :email"),
    {"email": "finance@helm.com"}
)
user = result.fetchone()

if user:
    print(f"\nVerification:")
    print(f"Email: {user[0]}")
    print(f"Hash (first 30 chars): {user[1][:30]}...")
    
    # Test verification
    is_valid = bcrypt.checkpw(password.encode('utf-8'), user[1].encode('utf-8'))
    print(f"Password verification test: {'✓ PASS' if is_valid else '✗ FAIL'}")

session.close()
