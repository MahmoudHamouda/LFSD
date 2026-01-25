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




@router.get("/", summary="List audits", response_model=dict[str, Any])
@limiter.limit("20/minute")
async def list_audits(
    *,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    cursor: Optional[str] = Query(None),
) -> dict[str, Any]:
    """Return a paginated list of audits for the authenticated user and/or system admins."""
    # Ensure AuditLog model is imported
    from models.logging_models import AuditLog
    
    # Filter by user (actors can see their own actions, or maybe restrict to admin? 
    # Usually audit logs are for admins, but let's assume personal audit trail if not admin)
    query = db.query(AuditLog)
    
    # If not admin, restrict to own actions
    if getattr(current_user, "role", "user") != "admin":
        query = query.filter(AuditLog.actor_id == current_user.id)
    
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
                    "timestamp": item.timestamp.isoformat(),
                    "details": item.changes_json
                } for item in items
            ], 
            "next_cursor": next_cursor
        }
    }
