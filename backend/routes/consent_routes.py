"""
Consent capture/query endpoints for the Responsible-AI governance layer.

These let the frontend capture and check a user's consent for AI-assisted
advisory. Authenticated; the user can only read/write their own consent. The
underlying store is append-only and tamper-evident (see responsible_ai).
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from core.authentication import get_current_user
from models.models import User
from services import governance_bridge as gov

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/consent", tags=["consent"])


class ConsentRequest(BaseModel):
    granted: bool
    purpose: Optional[str] = None


@router.get("")
async def get_consent(
    purpose: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """Return whether the current user has consent on file for a purpose."""
    return {
        "purpose": purpose or "ai_advisory",
        "has_consent": gov.has_consent(current_user.id, purpose),
    }


@router.post("", status_code=201)
async def set_consent(
    data: ConsentRequest,
    current_user: User = Depends(get_current_user),
):
    """Record (grant or withdraw) consent for the current user."""
    try:
        gov.record_consent(
            user_id=current_user.id,
            granted=data.granted,
            purpose=data.purpose,
            source="app",
        )
    except Exception as e:
        logger.error(f"Consent capture failed: {e}")
        raise HTTPException(
            status_code=503, detail="Consent service is currently unavailable."
        )
    return {
        "status": "recorded",
        "granted": data.granted,
        "purpose": data.purpose or "ai_advisory",
    }


@router.get("/history")
async def consent_history(
    purpose: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """The current user's consent grant/withdrawal history for a purpose."""
    return {
        "purpose": purpose or "ai_advisory",
        "history": gov.consent_history(current_user.id, purpose),
    }


@router.get("/activity")
async def consent_activity(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
):
    """Recent AI governance decisions logged for the current user."""
    return {"activity": gov.decision_activity(current_user.id, min(limit, 100))}
