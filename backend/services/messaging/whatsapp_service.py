"""
WhatsApp Cloud API Service for LFSD.
Handles sending messages via WhatsApp Business API (Graph API).
Hardened for production with validation, shared client, and resilient error handling.
"""

import httpx
import logging
import uuid
import hmac
import hashlib
import re
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

import core.config
from .base_messaging_service import BaseMessagingService, MessageResponse

logger = logging.getLogger(__name__)


class WhatsAppService(BaseMessagingService):
    """
    Service for WhatsApp Cloud API integration.
    Supports text and template messages.
    """

    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        """
        Initialize the service.
        Guards against missing credentials without crashing during boot.
        """
        self.settings = core.config.get_settings()
        self.access_token = self.settings.WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = self.settings.WHATSAPP_PHONE_NUMBER_ID
        self.version = self.settings.WHATSAPP_API_VERSION or "v22.0"
        self.verify_token = self.settings.WHATSAPP_VERIFY_TOKEN

        # Base URL constructed securely from settings
        self.base_url = (
            f"https://graph.facebook.com/{self.version}/{self.phone_number_id}"
        )

        # Support shared client for connection pooling
        self._client = client
        self._timeout = httpx.Timeout(15.0, connect=5.0)

    @property
    def provider_name(self) -> str:
        return "whatsapp"

    def _get_headers(self) -> Dict[str, str]:
        """Secured headers for Facebook Graph API."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Request-ID": str(uuid.uuid4()),
        }

    def _validate_phone(self, phone: str) -> str:
        """Enforce strict E.164-ish format (no plus, numeric only)."""
        sanitized = re.sub(r"\D", "", phone)
        if not (10 <= len(sanitized) <= 15):
            raise ValueError(f"Invalid phone number length: {phone}")
        return sanitized

    async def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Internal low-level request wrapper with error normalization."""
        if not self.access_token or not self.phone_number_id:
            raise RuntimeError("WhatsApp credentials not configured")

        url = f"{self.base_url}/{path}"
        headers = self._get_headers()

        # Use shared client or one-off
        async with self._client or httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.request(method, url, headers=headers, **kwargs)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                error_data = e.response.json().get("error", {})
                logger.error(f"WhatsApp API Error: {error_data.get('message', str(e))}")
                raise
            except Exception as e:
                logger.error(f"WhatsApp Connection Error: {e}")
                raise

    async def send_text_message(
        self, to: str, message: str, user_id: Optional[str] = None, **kwargs
    ) -> MessageResponse:
        """Sends a standard text message."""
        try:
            # 1. Validation
            to_formatted = self._validate_phone(to)
            msg_body = (message or "").strip()
            if not msg_body or len(msg_body) > 4096:
                return MessageResponse(
                    success=False,
                    provider=self.provider_name,
                    status="failed",
                    error="Message empty or too long",
                )

            # 2. Payload
            payload = {
                "messaging_product": "whatsapp",
                "to": to_formatted,
                "type": "text",
                "text": {"body": msg_body},
            }

            # 3. Request
            data = await self._request("POST", "messages", json=payload)

            # 4. Result
            msg_id = data.get("messages", [{}])[0].get("id")
            logger.info(f"WhatsApp Text sent: {msg_id} to {to_formatted}")

            return MessageResponse(
                success=True,
                message_id=msg_id,
                provider=self.provider_name,
                status="sent",
                metadata={"user_id": user_id} if user_id else {},
            )

        except Exception as e:
            return MessageResponse(
                success=False,
                provider=self.provider_name,
                status="failed",
                error=str(e),
            )

    async def send_template_message(
        self,
        to: str,
        template_name: str,
        template_params: Optional[List[Dict[str, Any]]] = None,
        language_code: str = "en_US",
        user_id: Optional[str] = None,
        **kwargs,
    ) -> MessageResponse:
        """Sends a structured template message."""
        try:
            to_formatted = self._validate_phone(to)

            payload = {
                "messaging_product": "whatsapp",
                "to": to_formatted,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {"code": language_code},
                },
            }

            if template_params:
                payload["template"]["components"] = [
                    {"type": "body", "parameters": template_params}
                ]

            data = await self._request("POST", "messages", json=payload)
            msg_id = data.get("messages", [{}])[0].get("id")

            return MessageResponse(
                success=True,
                message_id=msg_id,
                provider=self.provider_name,
                status="sent",
            )

        except Exception as e:
            return MessageResponse(
                success=False,
                provider=self.provider_name,
                status="failed",
                error=str(e),
            )

    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """Verification handshake for Hub subscriptions."""
        if mode == "subscribe" and token == self.verify_token:
            return challenge
        return None

    def validate_signature(self, payload: bytes, signature_header: str) -> bool:
        """Validates X-Hub-Signature-256 for event authenticity."""
        if not signature_header or not self.settings.SECRET_KEY:
            return False

        if "=" not in signature_header:
            return False

        sha_name, signature = signature_header.split("=")
        if sha_name != "sha256":
            return False

        mac = hmac.new(
            self.settings.SECRET_KEY.encode(), msg=payload, digestmod=hashlib.sha256
        )
        return hmac.compare_digest(mac.hexdigest(), signature)
