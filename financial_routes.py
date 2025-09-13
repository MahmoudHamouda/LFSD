"""
Financial service endpoints.

Contains endpoints for retrieving and managing financial data. These stubs
should be replaced with real implementations that integrate with payment
providers or accounting systems. Authentication and rate limiting are applied
globally.
"""

from typing import Any, Optional

from fastapi import APIRouter, Depends, Query

from authentication import get_current_user
from rate_limiting import limiter


router = APIRouter(prefix="/financial", tags=["Financial"])


@router.get("/balances", summary="Get account balances")
@limiter.limit("10/minute")
async def get_balances(
    *,
    current_user=Depends(get_current_user),
) -> dict[str, Any]:
    """Return dummy account balances for the current user."""
    return {"data": {"balances": {"USD": 0.0}}}


@router.get("/transactions", summary="List transactions")
@limiter.limit("15/minute")
async def list_transactions(
    *,
    current_user=Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    cursor: Optional[str] = Query(None),
) -> dict[str, Any]:
    """Return a paginated list of transactions."""
    return {"data": {"items": [], "next_cursor": None}}