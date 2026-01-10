import uuid
from datetime import datetime
print("DEBUG: LOADED HISTORY ROUTES V2")
import sys
sys.stdout.flush()
from typing import List, Any
from loguru import logger
from fastapi import APIRouter, HTTPException, Response, Depends, Request
from sqlalchemy.orm import Session
from models.database import get_db
from models.models import DBConversation, DBMessage, DBFinancial, DBTransaction, DBOrder, DBNotification, DBActivity
from core.authentication import get_current_user
from models.api_models import (
    Conversation,
    ChatMessage,
    HistoryListResponse,
    HistoryReadRequest,
    HistoryGenerateRequest,
    HistoryUpdateRequest,
    HistoryDeleteRequest,
    HistoryClearRequest,
    HistoryRenameRequest,
    MessageFeedbackRequest,
    CosmosDBHealth
)
import traceback
import sys
sys.path.append('services')
from services.uber_service import get_uber_service

router = APIRouter(prefix="/history")

@router.get("/list")
async def list_history(offset: int = 0, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    # Query conversations for current user ordered by date desc
    conversations = db.query(DBConversation).filter(DBConversation.user_id == current_user.id).order_by(DBConversation.date.desc()).all()
    return [
        HistoryListResponse(id=c.id, title=c.title, createdAt=c.date.isoformat())
        for c in conversations
    ]

@router.post("/read")
async def read_history(request: HistoryReadRequest, db: Session = Depends(get_db)):
    conversation = db.query(DBConversation).filter(DBConversation.id == request.conversation_id).first()
    if not conversation:
        return {"messages": []}
    
    # Convert DB models to Pydantic models
    messages = [
        ChatMessage(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            date=msg.date.isoformat(),
            feedback=msg.feedback
        )
        for msg in conversation.messages
    ]
    
    return Conversation(
        id=conversation.id,
        title=conversation.title,
        messages=messages,
        date=conversation.date.isoformat()
    )

from core.authentication import get_current_user

@router.post("/generate")
async def generate_history(request: Request, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    print("DEBUG: HANDLE HISTORY REQUEST START")
    import sys
    sys.stdout.flush()
    """
    Generate AI response for chat messages.
    Saves conversation to database and returns AI response.
    """
    import logging
    import sys
    
    # Configure explicit file logging
    debug_logger = logging.getLogger("debug_history")
    debug_logger.setLevel(logging.DEBUG)
    if not debug_logger.handlers:
        fh = logging.FileHandler("debug_history.log")
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        debug_logger.addHandler(fh)
    
    debug_logger.info("Generate history endpoint called")
    
    if not current_user:
        logger.warning("Auth - UNAUTHORIZED access to /history/generate")
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        # Parse request body
        try:
            body = await request.json()
            print(f"DEBUG: BODY: {body}")
            import sys
            sys.stdout.flush()
            debug_logger.info(f"Generate history request body: {body}")
        except Exception as e:
            debug_logger.error(f"Failed to parse request body: {e}")
            raise HTTPException(status_code=400, detail="Invalid JSON body")

        messages_data = body.get("messages", [])
        conversation_id = body.get("conversation_id")
        
        debug_logger.info(f"Processing generation for conversation: {conversation_id}, messages: {len(messages_data)}")
        
        # Create or get conversation
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            title = "New Chat"
            if messages_data and len(messages_data) > 0:
                first_content = messages_data[0].get("content", "")
                title = first_content[:30] if isinstance(first_content, str) else "New Chat"
            
            conversation = DBConversation(
                id=conversation_id,
                user_id=current_user.id,
                title=title,
                date=datetime.utcnow()
            )
            db.add(conversation)
            debug_logger.info(f"Created new conversation: {conversation_id}")
        else:
            conversation = db.query(DBConversation).filter(DBConversation.id == conversation_id).first()
            if not conversation:
                conversation = DBConversation(
                    id=conversation_id,
                    user_id=current_user.id,
                    title="New Chat",
                    date=datetime.utcnow()
                )
                db.add(conversation)
                debug_logger.info(f"Created missing conversation: {conversation_id}")
            else:
                conversation.date = datetime.utcnow()
                debug_logger.info(f"Updated existing conversation: {conversation_id}")
        
        # Save user messages to database
        for msg in messages_data:
            # Check if message already exists to avoid duplicates if frontend retries
            msg_id = msg.get("id") or str(uuid.uuid4())
            existing_msg = db.query(DBMessage).filter(DBMessage.id == msg_id).first()
            
            if not existing_msg:
                db_msg = DBMessage(
                    id=msg_id,
                    conversation_id=conversation_id,
                    user_id=current_user.id,
                    role=msg.get("role"),
                    content=msg.get("content") if isinstance(msg.get("content"), str) else str(msg.get("content")),
                    date=datetime.utcnow(),
                    feedback=msg.get("feedback")
                )
                db.add(db_msg)
        
        # Commit user messages before calling Gemini
        try:
            db.commit()
            debug_logger.info("Saved user messages to database")
        except Exception as e:
            debug_logger.error(f"Database commit failed: {e}")
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        
        # Generate AI response using Gemini
        try:
            print("DEBUG: Importing GeminiService...")
            from services.gemini_service import GeminiService
            import json
            
            gemini_service = GeminiService(db)
            
            # Prepare history for Gemini
            history = [{"role": msg.get("role"), "content": msg.get("content")} for msg in messages_data]
            context = {"user_id": current_user.id, "conversation_id": conversation_id}
            
            # Get response from Gemini (Returns JSON string now with usage)
            response_json = await gemini_service.generate_response(history, context)
            response_data_parsed = json.loads(response_json)
            response_text = response_data_parsed.get("text", "")
            usage = response_data_parsed.get("usage", {})
            
        except Exception as e:
            print(f"DEBUG: EXCEPTION IN HISTORY GEN: {e}")
            debug_logger.error(f"Gemini service error: {e}")
            response_text = f"I apologize, but I'm having trouble connecting to my AI services right now."
            usage = {"input_tokens": 0, "output_tokens": 0}
        
        # Create and save AI response message
        response_message_id = str(uuid.uuid4())
        db_response = DBMessage(
            id=response_message_id,
            conversation_id=conversation_id,
            user_id=current_user.id,
            role="assistant",
            content=response_text,
            date=datetime.utcnow(),
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            model_used=getattr(gemini_service, 'model_name', 'gemini-1.5-flash')
        )
        db.add(db_response)
        
        try:
            db.commit()
            debug_logger.info("Saved AI response to database")
        except Exception as e:
            debug_logger.error(f"Failed to save AI response: {e}")
            db.rollback()
            # We still return the response even if saving failed
        
        # Refresh conversation to get updated data
        try:
            db.refresh(conversation)
        except:
            pass # Ignore refresh errors
        
        # Return response in expected format
        response_data = {
            "choices": [
                {
                    "messages": [
                        {
                            "id": response_message_id,
                            "role": "assistant",
                            "content": response_text,
                            "date": datetime.utcnow().isoformat() + "Z"
                        }
                    ]
                }
            ],
            "history_metadata": {
                "conversation_id": conversation_id,
                "title": conversation.title,
                "date": conversation.date.isoformat()
            }
        }
        debug_logger.info("Returning successful response")
        return response_data

    except HTTPException:
        raise
    except Exception as e:
        debug_logger.error(f"Unhandled error in generate_history: {e}")
        traceback.print_exc()
        try:
            with open("critical_error.log", "a") as f:
                f.write(f"CRITICAL ERROR: {str(e)}\n")
                traceback.print_exc(file=f)
        except:
             pass
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update")
async def update_history(request: HistoryUpdateRequest, db: Session = Depends(get_db)):
    conversation = db.query(DBConversation).filter(DBConversation.id == request.conversation_id).first()
    if not conversation:
        return Response(status_code=404)
    
    # Clear old messages and add new ones
    db.query(DBMessage).filter(DBMessage.conversation_id == request.conversation_id).delete()
    for msg in request.messages:
        db_msg = DBMessage(
            id=msg.id,
            conversation_id=request.conversation_id,
            role=msg.role,
            content=msg.content if isinstance(msg.content, str) else str(msg.content),
            date=datetime.utcnow(),
            feedback=msg.feedback
        )
        db.add(db_msg)
    db.commit()
    return {"success": True}

@router.delete("/delete")
async def delete_history(request: HistoryDeleteRequest, db: Session = Depends(get_db)):
    conversation = db.query(DBConversation).filter(DBConversation.id == request.conversation_id).first()
    if not conversation:
        return Response(status_code=404)
    
    db.delete(conversation)
    db.commit()
    return {"success": True}

@router.delete("/delete_all")
async def delete_all_history(db: Session = Depends(get_db)):
    try:
        # Delete messages first to avoid FK constraint violations
        db.query(DBMessage).delete()
        db.query(DBConversation).delete()
        db.commit()
        return {"success": True}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/clear")
async def clear_history(request: HistoryClearRequest, db: Session = Depends(get_db)):
    conversation = db.query(DBConversation).filter(DBConversation.id == request.conversation_id).first()
    if not conversation:
        return Response(status_code=404)
    
    db.query(DBMessage).filter(DBMessage.conversation_id == request.conversation_id).delete()
    db.commit()
    return {"success": True}

@router.post("/rename")
async def rename_history(request: HistoryRenameRequest, db: Session = Depends(get_db)):
    conversation = db.query(DBConversation).filter(DBConversation.id == request.conversation_id).first()
    if not conversation:
        return Response(status_code=404)
    
    conversation.title = request.title
    db.commit()
    return {"success": True}

@router.get("/ensure")
async def ensure_history():
    return CosmosDBHealth(cosmosDB=True, status="CosmosDB is configured and working")

@router.post("/message_feedback")
async def message_feedback(request: MessageFeedbackRequest, db: Session = Depends(get_db)):
    message = db.query(DBMessage).filter(DBMessage.id == request.message_id).first()
    if message:
        message.feedback = request.message_feedback
        db.commit()
    return {"success": True}
