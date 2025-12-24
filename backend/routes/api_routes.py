import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, Request
from models.api_models import (
    ConversationRequest,
    UserInfo,
    FrontendSettings,
    UI,
    ChatMessage
)

router = APIRouter()

@router.get("/frontend_settings")
async def get_frontend_settings():
    return FrontendSettings(
        auth_enabled="false", # Disable auth for now to make it easier
        feedback_enabled="true",
        ui=UI(
            title="LFSD Chat",
            chat_title="Chat with LFSD",
            chat_description="Ask me anything about LFSD",
            show_share_button=True,
            show_chat_history_button=True
        ),
        sanitize_answer=False,
        oyd_enabled=False
    )

@router.get("/.auth/me")
async def get_auth_me():
    # Mock auth response
    return [UserInfo(
        access_token="mock_token",
        expires_on=datetime.now().isoformat(),
        id_token="mock_id_token",
        provider_name="mock_provider",
        user_claims=[],
        user_id="mock_user"
    )]

@router.post("/conversation")
async def conversation(request: ConversationRequest):
    # Echo back the last message for now
    last_message = request.messages[-1]
    
    response_message = ChatMessage(
        id=str(uuid.uuid4()),
        role="assistant",
        content=f"Echo: {last_message.content}",
        date=datetime.now().isoformat(),
        end_turn=True
    )
    
    return {
        "choices": [
            {
                "messages": [response_message]
            }
        ]
    }
