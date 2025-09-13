"""
Rate limiting middleware and configuration.

This module sets up slowapi's Limiter and exposes a Starlette middleware for
FastAPI. It tries to use a Redis backend if a REDIS_URL is configured; otherwise
it falls back to an in‑memory store. Endpoints can be decorated with
``@limiter.limit("20/minute")`` to override the default rate limit.
"""

from __future__ import annotations

from typing import Optional

from fastapi import Request
try:
    # Import from slowapi if available
    from slowapi import Limiter  # type: ignore
    from slowapi.errors import RateLimitExceeded  # type: ignore
    from slowapi.middleware import SlowAPIMiddleware  # type: ignore
    from slowapi.util import get_remote_address  # type: ignore
except Exception:
    # Provide no‑op fallbacks when slowapi is not installed. These simple
    # implementations allow the application to run without rate limiting.
    class Limiter:
        """
        Minimal Limiter stub used when slowapi is unavailable. The ``limit``
        decorator returned simply passes through the wrapped function.
        """

        def __init__(self, *args, **kwargs) -> None:
            pass

        def limit(self, *args, **kwargs):  # type: ignore[override]
            def decorator(func):
                return func

            return decorator

    class RateLimitExceeded(Exception):
        """
        Dummy exception used to mirror slowapi's RateLimitExceeded. Since
        throttling isn't enforced without slowapi, this exception is never
        raised in fallback mode.
        """

    class RateLimitMiddleware:
        """
        Minimal middleware that performs no rate limiting. It simply passes
        requests through to the underlying ASGI app. This class mimics the
        interface of SlowAPIMiddleware so application code does not crash.
        """

        def __init__(self, app, handler: Optional[callable] = None) -> None:  # type: ignore[override]
            self.app = app

        async def __call__(self, scope, receive, send) -> None:  # type: ignore[override]
            await self.app(scope, receive, send)

    def get_remote_address(request: Request) -> str:  # type: ignore[override]
        """
        Extract the remote IP address from a request. Provided for API
        compatibility when slowapi.util.get_remote_address is unavailable.
        """
        client = getattr(request, "client", None)
        return getattr(client, "host", "") if client else ""

try:
    # RedisStorage may raise if redis is unavailable
    from slowapi.storages.redis import RedisStorage
except Exception:
    RedisStorage = None  # type: ignore

from config import get_settings


settings = get_settings()

if RedisStorage and settings.REDIS_URL:
    try:
        storage = RedisStorage.from_url(settings.REDIS_URL)
    except Exception:
        storage = None
else:
    storage = None

if storage:
    limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT], storage=storage)
else:
    limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT])


# When slowapi is available we subclass SlowAPIMiddleware to enforce rate limits.
# When slowapi is unavailable the fallback RateLimitMiddleware above already provides
# a minimal implementation. In that case we avoid overriding the fallback class.
if 'SlowAPIMiddleware' in globals():
    class RateLimitMiddleware(SlowAPIMiddleware):  # type: ignore[misc]
        """
        Middleware to enforce rate limits on incoming requests.

        Inherits from SlowAPIMiddleware to integrate with FastAPI's middleware stack.
        """

        def __init__(self, app) -> None:
            super().__init__(app, handler=None)


__all__ = ["limiter", "RateLimitMiddleware", "RateLimitExceeded"]