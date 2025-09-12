from flask import request, jsonify
from functools import wraps
from collections import defaultdict, deque
import time

# In-memory store for rate limiting; keys are (IP, endpoint) and values are deques of timestamps
RATE_LIMIT_STORE = defaultdict(deque)

# Rate limit configuration per endpoint; 'window' in seconds and 'max_requests' allowed in that window
RATE_LIMITS = {
    "default": {"window": 60, "max_requests": 60},
}

def rate_limiter(endpoint):
    """
    Decorator for functions that need rate limiting.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
            config = RATE_LIMITS.get(endpoint, RATE_LIMITS["default"])
            window = config.get("window", 60)
            max_req = config.get("max_requests", 60)
            now = time.time()
            records = RATE_LIMIT_STORE[(user_ip, endpoint)]
            # purge old timestamps
            while records and now - records[0] > window:
                records.popleft()
            if len(records) >= max_req:
                return jsonify({"status": "error", "message": "Rate limit exceeded"}), 429
            records.append(now)
            return f(*args, **kwargs)
        return wrapper
    return decorator

def rate_limit_middleware(app):
    """
    Flask middleware to enforce rate limits on every request based on endpoint name.
    """
    @app.before_request
    def _enforce():
        ep = request.endpoint or "default"
        config = RATE_LIMITS.get(ep, RATE_LIMITS["default"])
        window = config.get("window", 60)
        max_req = config.get("max_requests", 60)
        user_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        now = time.time()
        records = RATE_LIMIT_STORE[(user_ip, ep)]
        while records and now - records[0] > window:
            records.popleft()
        if len(records) >= max_req:
            return jsonify({"status": "error", "message": "Rate limit exceeded"}), 429
        records.append(now)
    return



# Rate limit middleware that applies global limits to all endpoints

def rate_limit_middleware(app):
    """Apply global rate limiting before each request."""
    @app.before_request
    def _enforce_rate_limit():
        # Determine the endpoint name or use 'default'
        ep = request.endpoint or "default"
        # Fetch configuration for the endpoint or fall back to default
        config = RATE_LIMITS.get(ep, RATE_LIMITS.get("default", {}))
        window = config.get("window", config.get("period", 60))
        max_requests = config.get("max_requests", config.get("limit", 60))

        user_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        current_time = time.time()
        # Initialize list of timestamps for this IP and endpoint
        if isinstance(rate_limit_store, dict):
            # using dict for store
            timestamps = rate_limit_store.setdefault((user_ip, ep), [])
            # Remove timestamps older than the window
            rate_limit_store[(user_ip, ep)] = [t for t in timestamps if current_time - t <= window]
            timestamps = rate_limit_store[(user_ip, ep)]
            if len(timestamps) >= max_requests:
                return jsonify({"status": "error", "message": "Rate limit exceeded"}), 429
            timestamps.append(current_time)
        else:
            # using defaultdict(deque)
            records = rate_limit_store[(user_ip, ep)]
            while records and current_time - records[0] > window:
                records.popleft()
            if len(records) >= max_requests:
                return jsonify({"status": "error", "message": "Rate limit exceeded"}), 429
            records.append(current_time)
