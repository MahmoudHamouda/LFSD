"""
Base Messaging Service - Absolute interface for all messaging providers.

Defines the contract for messengers (WhatsApp, SMS, Slack, etc).
Implementations should be stateless and handle their own provider specifics.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class MessageResponse(BaseModel):
    """Standardized response for messaging operations."""

    success: bool
    message_id: Optional[str] = None
    provider: str
    status: str  # "sent", "failed", "pending"
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseMessagingService(ABC):
    """
    Abstract interface for all messaging providers.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider identifier (e.g., 'whatsapp', 'sms')."""

        raise NotImplementedError

    @abstractmethod
    async def send_text_message(
        self, to: str, message: str, user_id: Optional[str] = None, **kwargs
    ) -> MessageResponse:
        """Send a plain text message."""

        raise NotImplementedError

    @abstractmethod
    async def send_template_message(
        self,
        to: str,
        template_name: str,
        template_params: Optional[List[Dict[str, Any]]] = None,
        language_code: str = "en_US",
        user_id: Optional[str] = None,
        **kwargs
    ) -> MessageResponse:
        """Send a pre-approved template message."""

        raise NotImplementedError
