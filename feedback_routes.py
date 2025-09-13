"""
Feedback service endpoints.

Contains endpoints for submitting and retrieving feedback from users. All
endpoints in this router require authentication and may be rate limited.
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query

from authentication import get_current_user
from rate_limiting import limiter


router = APIRouter(prefix="/feedback", tags=["Feedback"])


@router.get("/", summary="List feedback entries")
@limiter.limit("20/minute")
async def list_feedback(
    *,
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
    current_user=Depends(get_current_user),
    message: str,
) -> dict[str, Any]:
    """Create a new feedback entry."""
    # TODO: save feedback message associated with current_user
    return {"data": {"message": message}}