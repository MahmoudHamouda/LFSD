"""
Activity feed endpoints.

Expose endpoints to retrieve user activity feeds.
"""

from typing import Any, Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from core.authentication import get_current_user
from core.rate_limiting import limiter
from models.database import get_db
from models.logging_models import ActivityFeed

router = APIRouter(prefix="/activity", tags=["Activity"])


@router.get("/feed", summary="Get activity feed")
@limiter.limit("30/minute")
async def get_activity_feed(
    *,
    request: Request,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(20, ge=1, le=100),
    cursor: Optional[str] = Query(None),
) -> dict[str, Any]:
    """Return a paginated activity feed for the current user."""

    query = db.query(ActivityFeed).filter(ActivityFeed.user_id == current_user.id)

    if cursor:
        query = query.filter(ActivityFeed.created_at < cursor)

    items = query.order_by(ActivityFeed.created_at.desc()).limit(limit).all()

    formatted_items = [
        {
            "id": item.id,
            "action": item.action_type,
            "description": item.description,
            "timestamp": item.created_at.isoformat(),
            "metadata": item.metadata_json,
        }
        for item in items
    ]

    next_cursor = None
    if items and len(items) == limit:
        next_cursor = items[-1].created_at.isoformat()

    return {"data": {"items": formatted_items, "next_cursor": next_cursor}}
