"""
WhatsApp webhook routes for LFSD.
Handles incoming WhatsApp messages and webhook verification.
"""
from fastapi import APIRouter, Request, HTTPException, Query
from fastapi.responses import PlainTextResponse
from typing import Dict, Any
import logging

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])
logger = logging.getLogger(__name__)


@router.get("/webhook")
async def verify_webhook(
    mode: str = Query(alias="hub.mode"),
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge")
) -> PlainTextResponse:
    """
    Verify WhatsApp webhook subscription.
    Facebook will call this endpoint to verify the webhook.
    """
    from services.messaging.whatsapp_service import WhatsAppService
    
    whatsapp = WhatsAppService()
    verified_challenge = whatsapp.verify_webhook(mode, token, challenge)
    
    if verified_challenge:
        logger.info("WhatsApp webhook verified successfully")
        return PlainTextResponse(content=verified_challenge)
    
    logger.warning("WhatsApp webhook verification failed")
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def receive_webhook(request: Request) -> Dict[str, str]:
    """
    Receive incoming WhatsApp messages.
    Facebook will POST to this endpoint when messages are received.
    """
    try:
        body = await request.json()
        logger.info(f"Received WhatsApp webhook: {body}")
        
        # Extract message data
        if body.get("object") == "whatsapp_business_account":
            entries = body.get("entry", [])
            
            for entry in entries:
                changes = entry.get("changes", [])
                
                for change in changes:
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    
                    for message in messages:
                        from_number = message.get("from")
                        message_type = message.get("type")
                        message_id = message.get("id")
                        
                        logger.info(f"Message from {from_number}: type={message_type}, id={message_id}")
                        
                        # Handle different message types
                        if message_type == "text":
                            text_body = message.get("text", {}).get("body")
                            logger.info(f"Text message: {text_body}")
                            
                            # Process message with Gemini AI
                            try:
                                from services.gemini_service import GeminiService
                                from services.messaging.whatsapp_service import WhatsAppService
                                from models.database import SessionLocal
                                
                                # Use a fresh session for this background-like processing
                                with SessionLocal() as db:
                                    gemini = GeminiService(db)
                                    # Identify user by phone number (from_number)
                                    # For now, we might need a lookup utility or assume from_number is the ID if we had phone auth
                                    # Fallback: Treat as anonymous or find user by phone (TODO: implement phone lookup)
                                    user_id = "whatsapp_user" 
                                    
                                    response_text = gemini.generate_response(user_id, text_body)
                                    
                                    # Send response back
                                    whatsapp_svc = WhatsAppService()
                                    whatsapp_svc.send_message(to_number=from_number, message_text=response_text)
                                    
                            except Exception as ai_error:
                                logger.error(f"AI processing failed: {ai_error}")
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
