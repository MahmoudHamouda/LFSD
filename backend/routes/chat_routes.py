"""
Chat service endpoints.

Provides endpoints for interacting with the chat subsystem. For long running
operations, consider offloading work via FastAPI's BackgroundTasks. The current
implementation only returns a static response.
"""

from typing import Any, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query

from core.authentication import get_current_user
from core.rate_limiting import limiter


router = APIRouter(prefix="/chat", tags=["Chat"])


def _send_message_async(message: str, user_id: str) -> None:
    """Background task to process chat messages."""
    from models.database import SessionLocal
    from models.chat_models import Message, Conversation
    from services.gemini_service import GeminiService
    import uuid
    from datetime import datetime

    db = SessionLocal()
    try:
        # 1. Ensure Conversation Exists (simple assumption: 1 active convo for now or create new)
        # For simplicity, let's create a new conversation id or find latest
        convo = (
            db.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(Conversation.date.desc())
            .first()
        )
        if not convo:
            convo = Conversation(
                id=str(uuid.uuid4()),
                user_id=user_id,
                title="New Chat",
                date=datetime.utcnow(),
            )
            db.add(convo)
            db.commit()

        # 2. Save User Message
        user_msg = Message(
            id=str(uuid.uuid4()),
            conversation_id=convo.id,
            user_id=user_id,
            role="user",
            content=message,
            date=datetime.utcnow(),
        )
        db.add(user_msg)
        db.commit()

        # 3. Generate AI Response
        gemini = GeminiService(db)
        ai_response_text = gemini.generate_response(user_id, message)

        # 4. Save AI Response
        ai_msg = Message(
            id=str(uuid.uuid4()),
            conversation_id=convo.id,
            user_id=user_id,
            role="assistant",
            content=ai_response_text,
            date=datetime.utcnow(),
        )
        db.add(ai_msg)
        db.commit()

    except Exception as e:
        print(f"Error in chat background task: {e}")
    finally:
        db.close()


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
    background_tasks.add_task(_send_message_async, message, current_user.id)
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
