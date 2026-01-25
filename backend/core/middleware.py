import uuid
import time
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp
from loguru import logger
from models.database import SessionLocal
from models.logging_models import BugReport, SystemLog, LogLevel, BugStatus
import traceback
import sys

class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Generates a unique Request ID for every incoming request and binds it to the logger context.
    """
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Bind request_id to the logger for this context
        with logger.contextualize(request_id=request_id):
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response

class BugReportMiddleware(BaseHTTPMiddleware):
    """
     catches unhandled exceptions, logs them, and creates a BugReport entry in the database.
    """
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        try:
            return await call_next(request)
        except Exception as exc:
            # 1. Log the error immediately
            logger.exception(f"Unhandled exception: {exc}")
            
            # 2. Extract Context
            request_id = getattr(request.state, "request_id", None)
            error_type = type(exc).__name__
            error_message = str(exc)
            stack_trace = "".join(traceback.format_exception(*sys.exc_info()))
            
            # 3. Save to Database
            try:
                db = SessionLocal()
                try:
                    bug = BugReport(
                        error_type=error_type,
                        error_message=error_message,
                        stack_trace=stack_trace,
                        request_id=request_id,
                        endpoint=str(request.url),
                        method=request.method,
                        system_info={"platform": sys.platform},
                        status=BugStatus.OPEN
                    )
                    db.add(bug)
                    db.commit()
                    db.refresh(bug)
                    bug_id = bug.id
                finally:
                    db.close()
            except Exception as db_exc:
                logger.error(f"Failed to save BugReport: {db_exc}")
                bug_id = "unknown"

            # 4. Return safe error response
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal Server Error",
                    "error_reference": f"BUG-{bug_id}",
                    "message": "The system encountered an unexpected error. Please provide the reference ID to support."
                }
            )
