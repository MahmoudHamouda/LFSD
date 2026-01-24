"""
Partner Service Models

Defines the persistence layer for Viv Partner Accounts.
Refactored for enterprise-grade integrity, performance, and auditability.
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean, Index, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import datetime

Base = declarative_base()

class Partner(Base):
    """
    Represents an integrated partner (e.g., Allianz, Fitness First).
    Hardened with uniqueness constraints, status management, and indexing.
    """
    __tablename__ = "partner_accounts_v2"
    
    # Primary Key with explicit autoincrement
    partner_id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Core Identity (Unique + Indexed)
    name = Column(String(150), nullable=False, unique=True, index=True)
    contact_email = Column(String(150), nullable=False, unique=True, index=True)
    phone_number = Column(String(30), nullable=True)
    
    # Categorization & Status
    status = Column(String(20), default="ACTIVE", index=True) # ACTIVE, INACTIVE, SUSPENDED
    category = Column(String(50), nullable=True, index=True) # INSURANCE, HEALTH, TRAVEL, etc.
    
    # Functional Data
    # Recommended: Use JSONB if on Postgres for better indexing, but JSON for compatibility
    services_offered = Column(JSON, nullable=False, default=list) 
    integration_config = Column(JSON, nullable=True) # API keys (encrypted), endpoints, etc.
    
    # Soft Delete Support
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Audit Trail (Timezone Aware)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(String(100), nullable=True) # Internal admin user Ref
    
    # Constraints & Indexes (Additional safety)
    __table_args__ = (
        # Ensure name and email are already unique, but Index helps performance
        Index('idx_partner_name_email', 'name', 'contact_email'),
    )

    def to_dict(self):
        """Standard serialization."""
        return {
            "partner_id": self.partner_id,
            "name": self.name,
            "contact_email": self.contact_email,
            "phone_number": self.phone_number,
            "status": self.status,
            "category": self.category,
            "services_offered": self.services_offered,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
