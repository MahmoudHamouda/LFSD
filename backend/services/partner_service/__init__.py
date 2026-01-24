"""
Partner Service Package

Manages integration partners, their service catalogs, and status tracking.
"""

from .models import Partner
from .db import get_db_session

__all__ = ["Partner", "get_db_session", "get_partner_service"]

class PartnerService:
    """
    Coordinator class for Partner operations.
    Can be used by other services (like GeminiService) to resolve partner info.
    """
    def __init__(self, db_session):
        self.db = db_session

    def get_partners_by_category(self, category: str):
        return self.db.query(Partner).filter(
            Partner.category == category,
            Partner.is_deleted == False
        ).all()

def get_partner_service(db_session) -> PartnerService:
    return PartnerService(db_session)
