"""
Notification service endpoints.

This router provides endpoints to fetch notifications and mark them as read.
Implement integration with your notification backend to persist and deliver
messages to users.
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query

from authentication import get_current_user
from rate_limiting import limiter


router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/", summary="List notifications")
@limiter.limit("30/minute")
async def list_notifications(
    *,
    current_user=Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    cursor: Optional[str] = Query(None),
) -> dict[str, Any]:
    """Return a paginated list of notifications for the current user."""
    return {"data": {"items": [], "next_cursor": None}}


@router.post("/read", summary="Mark notifications as read")
@limiter.limit("30/minute")
async def mark_notifications_read(
    *,
    current_user=Depends(get_current_user),
    notification_ids: list[str],
) -> dict[str, Any]:
    """Mark a list of notifications as read."""
    return {"data": {"read": notification_ids}}