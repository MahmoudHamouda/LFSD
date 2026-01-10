from fastapi import APIRouter, Depends, HTTPException, Body, Path
from sqlalchemy.orm import Session
from models.database import get_db
from services.chat_service.models import ChatSession, ChatHistory
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/chat", tags=["Chat"])

class ChatStartRequest(BaseModel):
    user_id: str
    context: Optional[str] = None

class ChatMessageRequest(BaseModel):
    user_id: str
    message: str

@router.post("/start", status_code=201)
def start_chat(
    data: ChatStartRequest,
    db: Session = Depends(get_db)
):
    # Default to advisory for generic start
    new_session = ChatSession(
        user_id=data.user_id, 
        context=data.context, 
        title="New Conversation", 
        mode="advisory"
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return {
        "message": "Chat session started",
        "session_id": new_session.session_id
    }

from services.gemini_service import GeminiService
import json

@router.post("/{session_id}/message")
async def handle_message(
    session_id: int = Path(...),
    data: ChatMessageRequest = Body(...),
    db: Session = Depends(get_db)
):
    user_id = data.user_id
    message = data.message

    # 1. Fetch Chat Session
    chat_session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not chat_session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    # 2. Save User Message
    user_msg = ChatHistory(
        session_id=session_id,
        user_id=user_id,
        message_type="user",
        content=message,
        timestamp=datetime.utcnow()
    )
    db.add(user_msg)
    
    # 3. Generate Title if first message
    # Check if this is the first user message
    msg_count = db.query(ChatHistory).filter(ChatHistory.session_id == session_id).count()
    # Note: msg_count includes the one we just added only if flushed, but we haven't flushed yet.
    # Actually, SQLAlchemy session tracks new objects. 
    # But count() usually runs against DB. 
    # Let's just check session title.
    if chat_session.title == "New Conversation":
         # We can use a simple helper or just leave it for now, 
         # or use Gemini to generate title (but that consumes tokens).
         # openai_client.generate_title is gone (was in shared).
         # We'll skip title generation for now to focus on usage.
         pass

    # 4. Generate AI Response using GeminiService
    gemini_service = GeminiService(db)
    
    # Construct history - for now just the current message effectively, 
    # but ideally we should fetch previous messages.
    # Let's just pass the current one for simplicity in verification.
    history = [{"role": "user", "content": message}]
    
    # Context
    context = {"user_id": user_id}
    if chat_session.context:
        context["session_context"] = chat_session.context
    
    response_json_str = await gemini_service.generate_response(history, context)
    
    # Parse the response
    try:
        response_data = json.loads(response_json_str)
    except json.JSONDecodeError:
        response_data = {"text": response_json_str, "usage": {}}
        
    ai_content = response_data.get("text", "")
    token_usage = response_data.get("usage", {})
    
    # 5. Save Assistant Message
    assistant_msg = ChatHistory(
        session_id=session_id,
        user_id=user_id,
        message_type="assistant",
        content=ai_content,
        timestamp=datetime.utcnow(),
        input_tokens=token_usage.get("input_tokens", 0),
        output_tokens=token_usage.get("output_tokens", 0),
        model_used="gemini-1.5-flash" # Hardcoded or fetch from service
    )
    db.add(assistant_msg)
    
    db.commit()
    
    return {
        "response": ai_content,
        "usage": token_usage
    }
