Defines the database models for users and related entities.
```python
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    first_name = Column(String(50))
    last_name = Column(String(50))
    email = Column(String(100), unique=True, nullable=False)
    phone_number = Column(String(20))
    gender = Column(String(10))
    date_of_birth = Column(DateTime)
    preferences = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class FamilyMember(Base):
    __tablename__ = "family_members"

    family_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    related_user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    relationship = Column(String(50))
    name = Column(String(50))
    date_of_birth = Column(DateTime)

class SocialAccount(Base):
    __tablename__ = "social_accounts"

    account_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    provider = Column(String(50))  # e.g., "Google", "Facebook"
    account_identifier = Column(String(100))  # Unique identifier for the account
    linked_at = Column(DateTime, default=datetime.datetime.utcnow)