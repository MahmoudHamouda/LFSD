"""
Pipeline Cache — Unified Caching Layer with Event-Driven Invalidation.

Cache keys are versioned: ctx:{user_id}:{version} to prevent stale reads.
Invalidation is event-driven: mutations in the system trigger targeted cache busts.

Three cache namespaces:
    - ctx:{user_id}:{version} — ContextFrame (5-min TTL)
    - intent:{hash}           — IntentResult (60s TTL)
    - resp:{template}:{hash}  — Response fragments (5-min TTL)

Uses Redis as primary backend (via REDIS_URL config).
Falls back to in-memory dict when Redis is unavailable.
"""

from __future__ import annotations

import hashlib
import logging
import time
from enum import Enum
from typing import Any, Dict, List, Optional, Type, TypeVar

from pydantic import BaseModel

logger = logging.getLogger("intelligence.cache")

T = TypeVar("T", bound=BaseModel)

# Default TTLs in seconds
DEFAULT_TTLS = {
    "ctx": 300,  # 5 minutes
    "intent": 60,  # 1 minute
    "resp": 300,  # 5 minutes
}


# ============================================================================
# Invalidation Events
# ============================================================================


class InvalidationEvent(str, Enum):
    """
    Events that trigger cache invalidation.

    Each event maps to specific namespaces that become stale.
    Wire these from your service layer — whenever one of these
    events occurs, call cache.invalidate_on_event(user_id, event).
    """

    TRANSACTION_LOGGED = "transaction_logged"  # Financial data changed
    ORDER_CREATED = "order_created"  # New order/booking
    ORDER_UPDATED = "order_updated"  # Order status change
    PREFERENCE_CHANGED = "preference_changed"  # User preferences changed
    CRISIS_MODE_TOGGLED = "crisis_mode_toggled"  # Crisis mode on/off
    HEALTH_SIGNAL_RECEIVED = "health_signal"  # New health data point
    GOAL_MODIFIED = "goal_modified"  # Goal created/updated/deleted
    SCORE_RECALCULATED = "score_recalculated"  # VivIndex scores changed


# Event → which cache namespaces to invalidate
_EVENT_INVALIDATION_MAP: Dict[InvalidationEvent, List[str]] = {
    InvalidationEvent.TRANSACTION_LOGGED: ["ctx", "resp"],
    InvalidationEvent.ORDER_CREATED: ["ctx", "resp"],
    InvalidationEvent.ORDER_UPDATED: ["ctx", "resp"],
    InvalidationEvent.PREFERENCE_CHANGED: ["ctx", "intent", "resp"],
    InvalidationEvent.CRISIS_MODE_TOGGLED: ["ctx", "intent", "resp"],  # Everything
    InvalidationEvent.HEALTH_SIGNAL_RECEIVED: ["ctx"],
    InvalidationEvent.GOAL_MODIFIED: ["ctx", "resp"],
    InvalidationEvent.SCORE_RECALCULATED: ["ctx"],
}


class PipelineCache:
    """
    Unified cache for the HELM pipeline.

    Primary: Redis (if available via REDIS_URL).
    Fallback: In-memory dict with TTL expiry.

    Cache keys are versioned per-user: ctx:{user_id}:{version}.
    Version is incremented on invalidation events to prevent stale reads.
    """

    def __init__(self, redis_url: Optional[str] = None):
        self._redis = None
        self._memory_store: Dict[str, tuple] = {}  # key -> (json_str, expiry_ts)
        self._version_store: Dict[str, int] = {}  # user_id -> version counter

        if redis_url:
            try:
                import redis

                self._redis = redis.Redis.from_url(
                    redis_url, decode_responses=True, socket_timeout=2
                )
                self._redis.ping()
                logger.info("Pipeline cache: Redis connected at %s", redis_url)
            except Exception as e:
                logger.warning(
                    "Pipeline cache: Redis unavailable (%s) — using in-memory fallback",
                    e,
                )
                self._redis = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, namespace: str, key: str, model_class: Type[T]) -> Optional[T]:
        """
        Retrieve a cached Pydantic model.

        For 'ctx' namespace, automatically appends current user version
        to the key for correctness.
        """
        full_key = self._build_key(namespace, key)
        json_str = self._get_raw(full_key)
        if json_str is None:
            return None
        try:
            return model_class.model_validate_json(json_str)
        except Exception as e:
            logger.warning("Cache deserialize error for %s: %s", full_key, e)
            self._delete_raw(full_key)
            return None

    def set(
        self,
        namespace: str,
        key: str,
        value: BaseModel,
        ttl: Optional[int] = None,
    ) -> None:
        """Cache a Pydantic model with versioned key."""
        full_key = self._build_key(namespace, key)
        ttl = ttl or DEFAULT_TTLS.get(namespace, 300)
        json_str = value.model_dump_json()
        self._set_raw(full_key, json_str, ttl)

    def invalidate(self, namespace: str, key: str) -> None:
        """Remove a specific cache entry."""
        full_key = self._build_key(namespace, key)
        self._delete_raw(full_key)

    def invalidate_user(self, user_id: str) -> None:
        """Invalidate all cached data for a user by bumping version."""
        self._bump_version(user_id)
        logger.info("Cache invalidated for user %s (version bumped)", user_id)

    def invalidate_on_event(self, user_id: str, event: InvalidationEvent) -> None:
        """
        Event-driven invalidation.

        Call this whenever a mutation event occurs in the system.
        Only invalidates the namespaces affected by that event type.

        Usage:
            cache.invalidate_on_event("user123", InvalidationEvent.TRANSACTION_LOGGED)
        """
        affected = _EVENT_INVALIDATION_MAP.get(event, ["ctx"])
        logger.info(
            "Cache invalidation: user=%s event=%s namespaces=%s",
            user_id,
            event.value,
            affected,
        )

        # If "ctx" is affected, bump user version (invalidates all versioned keys)
        if "ctx" in affected:
            self._bump_version(user_id)

        # Explicitly delete non-versioned entries if needed
        # (intent and resp are hash-keyed, they expire via TTL;
        #  but for preference/crisis changes, we nuke all user-specific keys)
        if "intent" in affected or "resp" in affected:
            self._delete_by_pattern(f"helm:intent:*{user_id}*")
            self._delete_by_pattern(f"helm:resp:*{user_id}*")

    # ------------------------------------------------------------------
    # Versioning
    # ------------------------------------------------------------------

    def get_user_version(self, user_id: str) -> int:
        """Get current cache version for a user."""
        # Try Redis
        if self._redis:
            try:
                v = self._redis.get(f"helm:ver:{user_id}")
                return int(v) if v else 0
            except Exception:
                pass
        return self._version_store.get(user_id, 0)

    def _bump_version(self, user_id: str) -> int:
        """Increment user's cache version counter."""
        ver_key = f"helm:ver:{user_id}"
        if self._redis:
            try:
                new_ver = self._redis.incr(ver_key)
                self._redis.expire(ver_key, 86400)  # 24h TTL on version key
                return new_ver
            except Exception:
                pass
        current = self._version_store.get(user_id, 0) + 1
        self._version_store[user_id] = current
        return current

    def _build_key(self, namespace: str, key: str) -> str:
        """Build cache key, adding version for context namespace."""
        if namespace == "ctx":
            version = self.get_user_version(key)  # key is user_id for ctx
            return f"helm:{namespace}:{key}:v{version}"
        return f"helm:{namespace}:{key}"

    # ------------------------------------------------------------------
    # Key generation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def hash_key(*parts: str) -> str:
        """Generate a deterministic hash key from parts."""
        combined = "|".join(str(p) for p in parts)
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    # ------------------------------------------------------------------
    # Backend: Redis or in-memory
    # ------------------------------------------------------------------

    def _get_raw(self, key: str) -> Optional[str]:
        """Get raw string from backend."""
        if self._redis:
            try:
                val = self._redis.get(key)
                if val is not None:
                    return val
                return None
            except Exception:
                pass

        entry = self._memory_store.get(key)
        if entry is None:
            return None
        json_str, expiry = entry
        if time.time() > expiry:
            del self._memory_store[key]
            return None
        return json_str

    def _set_raw(self, key: str, value: str, ttl: int) -> None:
        """Set raw string in backend."""
        if self._redis:
            try:
                self._redis.setex(key, ttl, value)
                return
            except Exception:
                pass
        self._memory_store[key] = (value, time.time() + ttl)

    def _delete_raw(self, key: str) -> None:
        """Delete from backend."""
        if self._redis:
            try:
                self._redis.delete(key)
            except Exception:
                pass
        self._memory_store.pop(key, None)

    def _delete_by_pattern(self, pattern: str) -> None:
        """Delete keys matching pattern (in-memory only, Redis uses SCAN)."""
        if self._redis:
            try:
                cursor = 0
                while True:
                    cursor, keys = self._redis.scan(cursor, match=pattern, count=100)
                    if keys:
                        self._redis.delete(*keys)
                    if cursor == 0:
                        break
            except Exception:
                pass

        # In-memory: delete matching keys
        to_delete = [k for k in self._memory_store if self._matches_pattern(k, pattern)]
        for k in to_delete:
            del self._memory_store[k]

    @staticmethod
    def _matches_pattern(key: str, pattern: str) -> bool:
        """Simple glob-like pattern matching for in-memory keys."""
        parts = pattern.split("*")
        if len(parts) == 1:
            return key == pattern
        pos = 0
        for i, part in enumerate(parts):
            if not part:
                continue
            idx = key.find(part, pos)
            if idx == -1:
                return False
            if i == 0 and idx != 0:
                return False
            pos = idx + len(part)
        return True

    @property
    def backend(self) -> str:
        """Which backend is active."""
        return "redis" if self._redis else "memory"

    def stats(self) -> Dict[str, Any]:
        """Simple cache stats for observability."""
        if self._redis:
            try:
                info = self._redis.info("keyspace")
                return {"backend": "redis", "info": info}
            except Exception:
                pass
        return {
            "backend": "memory",
            "entries": len(self._memory_store),
            "versions": len(self._version_store),
        }
