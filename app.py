"""
Application entry point and factory.

This module exposes a ``create_app`` function that instantiates and configures
the FastAPI application. It mounts middleware for CORS, rate limiting and
logging, sets up global exception handlers and registers routers for the
different service areas (audit, feedback, chat, recommendation, partner,
user, financial, notification and activity feed).
"""

from __future__ import annotations

from time import perf_counter
from typing import Callable, Optional

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
# Try to use loguru for structured logging; fall back to standard logging if not available.
try:
    from loguru import logger  # type: ignore
except Exception:
    import logging

    class _FallbackLogger(logging.Logger):  # type: ignore
        """
        Minimal logger API compatible with loguru. It exposes ``bind`` to mimic
        loguru's structured logging. The returned logger simply ignores bound
        context and uses the underlying logging.Logger methods for ``info`` and
        ``exception``.
        """

        def bind(self, **kwargs):
            # Ignore bound context; return the same logger instance
            return self

    # Configure root logger and get a named logger
    logging.basicConfig(level=logging.INFO)
    logger = _FallbackLogger(name="lfsd_app", level=logging.INFO)  # type: ignore

from config import get_settings
from rate_limiting import RateLimitExceeded, RateLimitMiddleware, limiter


def create_app() -> FastAPI:
    """Create and configure a FastAPI application."""
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

    # Rate limiting
    app.state.limiter = limiter
    app.add_middleware(RateLimitMiddleware)

    # Logging middleware
    @app.middleware("http")
    async def log_requests(request: Request, call_next: Callable) -> JSONResponse:
        start = perf_counter()
        logger.bind(method=request.method, path=request.url.path).info("Request received")
        try:
            response = await call_next(request)
        except Exception:
            # Let exception handlers deal with it; still log
            logger.exception("Unhandled error in request")
            raise
        finally:
            duration = perf_counter() - start
            logger.bind(status=getattr(response, "status_code", None), duration=duration).info(
                "Request completed"
            )
        return response

    # Exception handlers
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Return errors in a consistent JSON shape."""
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": str(exc.status_code), "message": exc.detail}},
        )

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={
                "error": {
                    "code": "rate_limit_exceeded",
                    "message": "Too many requests, please slow down.",
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_server_error",
                    "message": "An unexpected error occurred.",
                }
            },
        )

    # Health endpoint
    @app.get("/healthz", tags=["Health"])
    async def healthz() -> dict[str, str]:
        settings = get_settings()
        return {"status": "ok", "env": settings.ENV}

    # Import and include routers. Import within the function to avoid circular deps.
    from audit_routes import router as audit_router
    from feedback_routes import router as feedback_router
    from chat_routes import router as chat_router
    from recommendation_routes import router as recommendation_router
    from partner_routes import router as partner_router
    from user_routes import router as user_router
    from financial_routes import router as financial_router
    from notification_routes import router as notification_router
    from activity_feed_routes import router as activity_feed_router

    for r in [
        audit_router,
        feedback_router,
        chat_router,
        recommendation_router,
        partner_router,
        user_router,
        financial_router,
        notification_router,
        activity_feed_router,
    ]:
        app.include_router(r)

    return app


# Uvicorn entry point when running directly (not used in production under Gunicorn)
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:create_app",
        factory=True,
        host="0.0.0.0",
        port=8000,
        reload=False,
    )