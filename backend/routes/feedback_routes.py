"""
Feedback service endpoints.

Contains endpoints for submitting and retrieving feedback from users. All
endpoints in this router require authentication and may be rate limited.
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query, Request

from core.authentication import get_current_user
from core.rate_limiting import limiter


router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.get("/", summary="List feedback entries")
@limiter.limit("20/minute")
async def list_feedback(
    *,
    request: Request,
    current_user=Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    cursor: Optional[str] = Query(None),
) -> dict[str, Any]:
    """Return a paginated list of feedback messages."""
    return {"data": {"items": [], "next_cursor": None}}


@router.post("/", summary="Submit feedback")
@limiter.limit("10/minute")
async def create_feedback(
    *,
    request: Request,
    current_user=Depends(get_current_user),
    message: str,
) -> dict[str, Any]:
    """Create a new feedback entry."""
    from core.observability import Observability
    
    Observability.send_notification(
        user_id="admin", # Send to admin
        subject=f"New Feedback from {current_user.email}",
        body=message,
        channel="system",
        priority="normal",
        payload={"reporter_id": current_user.id, "message": message}
    )
    
    return {"data": {"message": "Feedback received"}}
