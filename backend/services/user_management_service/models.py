"""
User Management Service Models

Defines the persistence layer for Viv User profiles, family connections, 
and social identity links.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Index, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

class User(Base):
    """
    Main User record for the system.
    Refactored with status tracking, soft-delete, and timezone-aware audit logs.
    """
    __tablename__ = "users_service_v3"

    user_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Profile Data
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    email = Column(String(150), unique=True, nullable=False, index=True)
    phone_number = Column(String(30), nullable=True)
    gender = Column(String(20), nullable=True)
    date_of_birth = Column(DateTime(timezone=True), nullable=True)
    
    # Account Status & Logic
    status = Column(String(20), default="ACTIVE", index=True) # ACTIVE, SUSPENDED, PENDING
    preferences = Column(JSON, nullable=False, server_default='{}')
    
    # Soft Delete Support
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # Auditing (Timezone Aware)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    family_members = relationship(
        "FamilyMember",
        foreign_keys="FamilyMember.user_id",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    social_accounts = relationship(
        "SocialAccount",
        back_populates="user",
        cascade="all, delete-orphan"
    )


class FamilyMember(Base):
    """Tracks relationship links between users or to non-user family profiles."""
    __tablename__ = "family_members_v2"

    family_id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(String, ForeignKey("users_service_v3.user_id"), nullable=False, index=True)
    related_user_id = Column(String, ForeignKey("users_service_v3.user_id"), nullable=True)

    relationship_type = Column(String(50), nullable=True) # PARENT, CHILD, SPOUSE
    name = Column(String(100), nullable=True)
    date_of_birth = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="family_members"
    )

    related_user = relationship(
        "User",
        foreign_keys=[related_user_id]
    )


class SocialAccount(Base):
    """Links to external identities (Google, FB, etc.)."""
    __tablename__ = "social_accounts_v2"

    account_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users_service_v3.user_id"), nullable=False, index=True)

    provider = Column(String(50), nullable=False)  # Google, Facebook, Apple
    account_identifier = Column(String(150), nullable=False, index=True)
    
    linked_at = Column(DateTime(timezone=True), server_default=func.now())
    metadata_json = Column(JSON, nullable=True)

    user = relationship("User", back_populates="social_accounts")
