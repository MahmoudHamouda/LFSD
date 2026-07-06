import json
import logging
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from models.api_models import (
    ConversationRequest,
    UserInfo,
    FrontendSettings,
    UI,
    ChatMessage,
)
from models.database import get_db
from models.models import User as DBUser
from core.authentication import get_optional_user

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/frontend_settings")
async def get_frontend_settings():
    return FrontendSettings(
        auth_enabled="false",  # Disable auth for now to make it easier
        feedback_enabled="true",
        ui=UI(
            title="LFSD Chat",
            chat_title="Chat with LFSD",
            chat_description="Ask me anything about LFSD",
            show_share_button=True,
            show_chat_history_button=True,
        ),
        sanitize_answer=False,
        oyd_enabled=False,
    )


@router.get("/.auth/me")
async def get_auth_me():
    # Mock auth response
    return [
        UserInfo(
            access_token="mock_token",
            expires_on=datetime.now().isoformat(),
            id_token="mock_id_token",
            provider_name="mock_provider",
            user_claims=[],
            user_id="mock_user",
        )
    ]


@router.post("/conversation")
async def conversation(
    request: ConversationRequest,
    db: Session = Depends(get_db),
    current_user: Optional[DBUser] = Depends(get_optional_user),
):
    """
    Primary chat surface consumed by the frontend.

    Drives the full HELM decision engine (Orchestrator -> Intelligence
    Pipeline -> legacy fallback) via ``GeminiService.generate_response`` and
    maps the result into the ``{choices: [{messages: [...]}]}`` shape the
    frontend expects. Signed-in users get personalized, data-backed answers;
    unauthenticated visitors still get engine-driven responses.
    """
    if not request.messages:
        return _assistant_reply("Please send a message to get started.")

    # Deferred import keeps route import lightweight and avoids circular imports.
    from services.gemini_service import GeminiService

    # Preserve full conversation history so the engine has context.
    history = [
        {"role": m.role, "content": m.content}
        for m in request.messages
        if m.content is not None
    ]

    user_id = current_user.id if current_user else "guest"
    context = {"user_id": user_id}
    if request.conversation_id:
        context["session_id"] = request.conversation_id

    try:
        gemini_service = GeminiService(db)
        response_json_str = await gemini_service.generate_response(history, context)

        try:
            response_data = json.loads(response_json_str)
        except (json.JSONDecodeError, TypeError):
            response_data = {"text": response_json_str}

        ai_content = response_data.get("text") or ""
        if not ai_content:
            ai_content = (
                "I'm sorry, I couldn't generate a response just now. Please try again."
            )
    except Exception as e:
        logger.error(f"Error generating conversation response: {e}", exc_info=True)
        ai_content = (
            "I'm having trouble reaching my reasoning engine right now. "
            "Please try again in a moment."
        )

    return _assistant_reply(ai_content)


def _assistant_reply(content: str) -> dict:
    """Wrap assistant text in the frontend's expected choices/messages shape."""
    response_message = ChatMessage(
        id=str(uuid.uuid4()),
        role="assistant",
        content=content,
        date=datetime.now().isoformat(),
        end_turn=True,
    )
    return {"choices": [{"messages": [response_message]}]}
