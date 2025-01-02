from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    email = Column(String(100), unique=True, nullable=False)
    phone_number = Column(String(20), nullable=True)
    gender = Column(String(10), nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    preferences = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    family_members = relationship("FamilyMember", back_populates="user", cascade="all, delete-orphan")
    social_accounts = relationship("SocialAccount", back_populates="user", cascade="all, delete-orphan")


class FamilyMember(Base):
    __tablename__ = "family_members"

    family_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    related_user_id = Column(Integer, ForeignKey("users.user_id"), nullable=True)
    relationship = Column(String(50), nullable=True)
    name = Column(String(50), nullable=True)
    date_of_birth = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="family_members")


class SocialAccount(Base):
    __tablename__ = "social_accounts"

    account_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    provider = Column(String(50), nullable=False)  # e.g., "Google", "Facebook"
    account_identifier = Column(String(100), nullable=False)  # Unique identifier for the account
    linked_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="social_accounts")
