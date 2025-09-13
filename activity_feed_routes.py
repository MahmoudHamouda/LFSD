"""
Activity feed endpoints.

Expose endpoints to retrieve user activity feeds. For now, the implementation
returns an empty list; integrate with your activity feed service to return
actual data.
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query

from authentication import get_current_user
from rate_limiting import limiter


router = APIRouter(prefix="/activity", tags=["Activity"])


@router.get("/feed", summary="Get activity feed")
@limiter.limit("30/minute")
async def get_activity_feed(
    *,
    current_user=Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    cursor: Optional[str] = Query(None),
) -> dict[str, Any]:
    """Return a paginated activity feed for the current user."""
    return {"data": {"items": [], "next_cursor": None}}