"""
Application entry point and factory.

This module exposes a ``create_app`` function that instantiates and configures
the FastAPI application. It mounts middleware for CORS, rate limiting and
logging, sets up global exception handlers and registers routers for the
different service areas.
"""

from __future__ import annotations

from time import perf_counter
from typing import Callable
import sys
import os

# Add current directory (backend) to sys.path so that absolute imports (e.g. 'from core') work.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import traceback

# Try to use loguru for structured logging; fall back to standard logging if not available.
try:
    from loguru import logger  # type: ignore
except Exception:
    import logging

    class _FallbackLogger(logging.Logger):  # type: ignore
        """
        Minimal logger API compatible with loguru. It exposes ``bind`` to mimic
        loguru's structured logging.
        """

        def bind(self, **kwargs):
            return self

    logging.basicConfig(level=logging.INFO)
    logger = _FallbackLogger(name="lfsd_app", level=logging.INFO)  # type: ignore

from core.config import get_settings
from core.rate_limiting import RateLimitExceeded, RateLimitMiddleware, limiter


from core.logging_config import setup_logging
from core.middleware import RequestIDMiddleware, BugReportMiddleware

def create_app() -> FastAPI:
    """Create and configure a FastAPI application."""
    setup_logging() # Configure structured logging
    
    settings = get_settings()
    app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

    # CORS configuration
    if settings.ALLOWED_ORIGINS == "*":
        allow_origins = ["*"]
    else:
        allow_origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",") if origin.strip()]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom Middleware
    app.add_middleware(BugReportMiddleware)
    app.add_middleware(RequestIDMiddleware) # Should be outer to capture everything

    # Rate limiting
    app.state.limiter = limiter
    # app.add_middleware(RateLimitMiddleware)

    # Exception handlers
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Return errors in a consistent JSON shape."""
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests, please slow down."},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        import traceback
        error_details = f"Internal Server Error: {str(exc)}"
        # logger.exception("Unhandled exception") # Already logged
        print(f"CRITICAL ERROR: {error_details}")
        print(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"detail": error_details},
        )

    # Register routers
    from routes import (
        api_routes_time,
        api_routes_health,
        api_routes_finance,
        api_routes_lifestyle,
        history_routes,
        user_routes,
        calendar_routes,
        api_routes_onboarding,
        api_routes_scores,
    )
    
    # Ensure mappers are configured
    from sqlalchemy.orm import configure_mappers
    configure_mappers()

    app.include_router(api_routes_time.router, prefix="/api")
    app.include_router(api_routes_health.router) # Prefix is already in router definition
    app.include_router(api_routes_finance.router, prefix="/api")
    app.include_router(api_routes_lifestyle.router, prefix="/api")
    app.include_router(history_routes.router)
    app.include_router(user_routes.router, prefix="/api")
    app.include_router(calendar_routes.router)
    app.include_router(api_routes_onboarding.router, prefix="/api")
    app.include_router(api_routes_onboarding.router, prefix="/api")
    app.include_router(api_routes_scores.router, prefix="/api/scores")
    
    from routes import api_routes_goals
    app.include_router(api_routes_goals.router, prefix="/api")
    
    from routes import api_routes_auth
    app.include_router(api_routes_auth.router, prefix="/api")

    from routes import api_routes_session
    app.include_router(api_routes_session.router, prefix="/api")
    app.include_router(api_routes_session.user_router, prefix="/api")

    # Initialize Scheduler
    from services.scheduler_service import SchedulerService
    scheduler = SchedulerService()
    
    @app.on_event("startup")
    async def startup_event():
        scheduler.start()
        
    @app.on_event("shutdown")
    async def shutdown_event():
        scheduler.stop()

    return app

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:create_app",
        factory=True,
        host="0.0.0.0",
        port=8003,
        reload=True,
    )