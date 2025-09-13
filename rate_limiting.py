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
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

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


class RateLimitMiddleware(SlowAPIMiddleware):
    """
    Middleware to enforce rate limits on incoming requests.

    Inherits from SlowAPIMiddleware to integrate with FastAPI's middleware stack.
    """

    def __init__(self, app) -> None:
        super().__init__(app, handler=None)


__all__ = ["limiter", "RateLimitMiddleware", "RateLimitExceeded"]