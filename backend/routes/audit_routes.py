"""
Audit service endpoints.

This module defines routes related to the audit domain. Endpoints require
authentication via JWT and are rate limited. Replace the stub implementations
with real business logic and persistent storage.
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query

from core.authentication import get_current_user
from core.rate_limiting import limiter
from sqlalchemy.orm import Session
from models.database import get_db


router = APIRouter(prefix="/audit", tags=["Audit"])


    from models.logging_models import AuditLog
    from models.database import get_db
    from sqlalchemy.orm import Session
    
    # Dependencies needed since they weren't in function signature originally
    # But for cleaner design, we should add db to function signature. 
    # Since I can't easily change signature in single replacement without risk,
    # I'll just rely on what's available or use the context (but depends won't work inside body)
    # Actually, let's just do a localized import and session creation if DB isn't passed,
    # OR better, let's assume I can modify the signature in a subsequent step or just use SessionLocal?
    # Wait, the best way in FastAPI is to add the dependency. I will rewrite the whole function signature lines 22-27.
    pass

@router.get("/", summary="List audits")
@limiter.limit("20/minute")
async def list_audits(
    *,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    cursor: Optional[str] = Query(None),
) -> dict[str, Any]:
    """Return a paginated list of audits for the authenticated user."""
    from models.logging_models import AuditLog
    
    query = db.query(AuditLog).filter(AuditLog.actor_id == current_user.id)
    
    if cursor:
        query = query.filter(AuditLog.timestamp < cursor)
        
    items = query.order_by(AuditLog.timestamp.desc()).limit(limit).all()
    
    # Calculate next cursor
    next_cursor = None
    if items and len(items) == limit:
        next_cursor = items[-1].timestamp.isoformat()

    return {
        "data": {
            "items": [
                {
                    "id": item.id,
                    "action": item.action,
                    "entity_type": item.entity_type,
                    "timestamp": item.timestamp,
                    "details": item.changes_json
                } for item in items
            ], 
            "next_cursor": next_cursor
        }
    }
