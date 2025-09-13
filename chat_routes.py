"""
Chat service endpoints.

Provides endpoints for interacting with the chat subsystem. For long running
operations, consider offloading work via FastAPI's BackgroundTasks. The current
implementation only returns a static response.
"""

from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query

from authentication import get_current_user
from rate_limiting import limiter


router = APIRouter(prefix="/chat", tags=["Chat"])


def _send_message_async(message: str) -> None:
    """Stubbed background task to process chat messages."""
    # TODO: integrate with chat service
    return None


@router.post("/messages", summary="Send a chat message")
@limiter.limit("30/minute")
async def send_message(
    *,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    message: str,
) -> dict[str, Any]:
    """
    Accept a chat message from the authenticated user and trigger asynchronous
    processing. Returns a 202 response indicating acceptance.
    """
    background_tasks.add_task(_send_message_async, message)
    return {"data": {"accepted": True}}


@router.get("/messages", summary="List recent chat messages")
@limiter.limit("60/minute")
async def list_messages(
    *,
    current_user=Depends(get_current_user),
    limit: int = Query(20, ge=1, le=100),
    cursor: Optional[str] = Query(None),
) -> dict[str, Any]:
    """Return a paginated list of chat messages."""
    return {"data": {"items": [], "next_cursor": None}}