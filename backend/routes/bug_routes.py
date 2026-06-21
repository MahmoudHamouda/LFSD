"""
Bug reporting endpoints.
"""

from typing import Any, Optional
from fastapi import APIRouter, Depends, Body, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from models.database import get_db
from services.bug_service import BugService
from core.rate_limiting import limiter
from core.authentication import get_current_user

router = APIRouter(prefix="/bugs", tags=["Bugs"])


class BugReportRequest(BaseModel):
    error_message: str
    stack_trace: str
    source_file: Optional[str] = None
    context: Optional[dict] = None
    user_id: Optional[str] = None


@router.post("/report", summary="Report a bug")
@limiter.limit("5/minute")
async def report_bug(
    *,
    request: Request,
    db: Session = Depends(get_db),
    payload: BugReportRequest,
    current_user=Depends(get_current_user)
) -> Any:
    """
    Submit a bug report.
    """
    service = BugService(db)

    # Enrich context with request headers if needed
    context = payload.context or {}
    context["user_agent"] = request.headers.get("user-agent")

    report = service.create_report(
        error_message=payload.error_message,
        stack_trace=payload.stack_trace,
        source_file=payload.source_file,
        context=context,
        user_id=current_user.id,  # Trust the token, not the payload
    )

    return {"status": "success", "report_id": report.id}
