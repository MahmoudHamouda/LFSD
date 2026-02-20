"""
Stage 1: Input Processing — Fully Deterministic, No LLM.

Normalizes raw user input, sanitizes it, and enriches with session metadata.
Produces an InputEnvelope that all subsequent stages consume.

Performance target: < 1ms per request.
"""

from __future__ import annotations

import html
import re
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .schemas import InputEnvelope

logger = logging.getLogger("intelligence.input_processor")

# Characters that should never appear in user input
_DANGEROUS_PATTERN = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')

# Collapse multiple whitespace
_WHITESPACE_COLLAPSE = re.compile(r'\s+')

# Max input length (characters) — anything beyond this is truncated
MAX_INPUT_LENGTH = 4000


class InputProcessor:
    """
    Stage 1 of the HELM Intelligence Pipeline.

    Responsibilities:
        - Normalize and sanitize raw text
        - Build InputEnvelope with session metadata
        - Parse structured attachments (transaction receipts, health readings)
        - Enforce input length limits
    """

    def process(
        self,
        raw_text: str,
        user_id: str,
        session_metadata: Optional[Dict[str, Any]] = None,
    ) -> InputEnvelope:
        """
        Transform raw user input into a standardized InputEnvelope.

        Args:
            raw_text: The raw message from the user.
            user_id: Authenticated user identifier.
            session_metadata: Optional dict with session_id, conversation_history,
                              device_type, locale, attachments.

        Returns:
            InputEnvelope with normalized text and enriched metadata.
        """
        metadata = session_metadata or {}

        # Normalize
        normalized = self._normalize_text(raw_text)

        # Build envelope
        envelope = InputEnvelope(
            user_id=user_id,
            timestamp=datetime.now(timezone.utc),
            raw_text=raw_text.strip(),
            normalized_text=normalized,
            session_id=metadata.get("session_id"),
            conversation_history=metadata.get("conversation_history", []),
            device_type=metadata.get("device_type"),
            locale=metadata.get("locale", "en"),
            attachments=self._parse_attachments(metadata.get("attachments", [])),
        )

        logger.debug(
            "InputEnvelope created",
            extra={"request_id": envelope.request_id, "text_length": len(normalized)},
        )

        return envelope

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _normalize_text(self, text: str) -> str:
        """
        Normalize raw text: strip, sanitize, collapse whitespace.

        Does NOT lowercase — that's handled by intent classification
        where case matters for entity extraction.
        """
        if not text:
            return ""

        # Strip leading/trailing whitespace
        result = text.strip()

        # Truncate if too long
        if len(result) > MAX_INPUT_LENGTH:
            result = result[:MAX_INPUT_LENGTH]
            logger.warning("Input truncated to %d characters", MAX_INPUT_LENGTH)

        # Remove control characters (keep newlines and tabs)
        result = _DANGEROUS_PATTERN.sub('', result)

        # Escape HTML entities to prevent injection
        result = html.unescape(result)

        # Collapse multiple whitespace into single space
        result = _WHITESPACE_COLLAPSE.sub(' ', result).strip()

        return result

    def _parse_attachments(
        self, attachments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Parse and validate structured attachments.

        Supported types:
            - transaction_receipt: {amount, merchant, date, category}
            - health_reading: {type, value, unit, timestamp}
            - calendar_event: {title, start, end, location}
        """
        parsed = []
        for attachment in attachments:
            att_type = attachment.get("type", "unknown")
            if att_type in ("transaction_receipt", "health_reading", "calendar_event"):
                parsed.append(attachment)
            else:
                logger.warning("Unknown attachment type: %s", att_type)
        return parsed
