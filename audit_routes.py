"""
Audit service endpoints.

This module defines routes related to the audit domain. Endpoints require
authentication via JWT and are rate limited. Replace the stub implementations
with real business logic and persistent storage.
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query

from authentication import get_current_user
from rate_limiting import limiter


router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("/", summary="List audits")
@limiter.limit("20/minute")
async def list_audits(
    *,
    current_user=Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    cursor: Optional[str] = Query(None),
) -> dict[str, Any]:
    """Return a paginated list of audits for the authenticated user."""
    # TODO: integrate with database
    return {"data": {"items": [], "next_cursor": None}}