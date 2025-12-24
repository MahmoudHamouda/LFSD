"""
WhatsApp Cloud API Service for LFSD.
Handles sending messages via WhatsApp Business API.
"""
import os
import httpx
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


class WhatsAppService:
    """Service for WhatsApp Cloud API integration."""
    
    def __init__(self):
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.base_url = f"https://graph.facebook.com/v22.0/{self.phone_number_id}"
        
        if not self.access_token or not self.phone_number_id:
            raise ValueError("WhatsApp credentials not configured in .env")
    
    async def send_template_message(
        self,
        to: str,
        template_name: str = "hello_world",
        language_code: str = "en_US"
    ) -> Dict[str, Any]:
        """
        Send a template message via WhatsApp.
        
        Args:
            to: Recipient phone number (with country code, no +)
            template_name: Name of the approved template
            language_code: Language code for the template
            
        Returns:
            API response dict
        """
        url = f"{self.base_url}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language_code
                }
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=10.0)
            response.raise_for_status()
            return response.json()
    
    async def send_text_message(
        self,
        to: str,
        message: str
    ) -> Dict[str, Any]:
        """
        Send a text message via WhatsApp.
        
        Args:
            to: Recipient phone number (with country code, no +)
            message: Text message to send
            
        Returns:
            API response dict
        """
        url = f"{self.base_url}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {
                "body": message
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=10.0)
            response.raise_for_status()
            return response.json()
    
    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """
        Verify webhook subscription.
        
        Args:
            mode: Verification mode
            token: Verification token
            challenge: Challenge string
            
        Returns:
            Challenge string if verification succeeds, None otherwise
        """
        verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "lfsd_webhook_verify_token")
        
        if mode == "subscribe" and token == verify_token:
            return challenge
        return None
