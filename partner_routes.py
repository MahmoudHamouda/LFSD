"""
Partner service endpoints.

This module contains endpoints related to partner integrations. All endpoints
require authentication and may be rate limited. Replace stub logic with
real partner onboarding and management features.
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query

from authentication import get_current_user
from rate_limiting import limiter


router = APIRouter(prefix="/partners", tags=["Partners"])


@router.get("/", summary="List partners")
@limiter.limit("10/minute")
async def list_partners(
    *,
    current_user=Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    cursor: Optional[str] = Query(None),
) -> dict[str, Any]:
    """Return a paginated list of partners."""
    return {"data": {"items": [], "next_cursor": None}}


@router.post("/", summary="Register a new partner")
@limiter.limit("5/minute")
async def register_partner(*, current_user=Depends(get_current_user), name: str) -> dict[str, Any]:
    """Register a new partner with the given name."""
    return {"data": {"name": name}}