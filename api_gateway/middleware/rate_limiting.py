from flask import request, jsonify
from functools import wraps
import time

# In-memory store for rate limiting (can use Redis for production)
rate_limit_store = {}

# Rate limit configuration
RATE_LIMITS = {
    "default": {"limit": 100, "period": 60},  # 100 requests per 60 seconds
    "/users/<int:user_id>/chat": {"limit": 50, "period": 60},  # Example per-endpoint limit
    "/providers": {"limit": 30, "period": 60},  # 30 requests per 60 seconds
    "/users/<int:user_id>/orders": {"limit": 20, "period": 60},  # 20 requests per 60 seconds
    "/users/<int:user_id>/financials/affordability": {"limit": 10, "period": 60},  # 10 requests per 60 seconds
}

def rate_limiter(endpoint):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            user_ip = request.remote_addr
            current_time = int(time.time())
            config = RATE_LIMITS.get(endpoint, RATE_LIMITS["default"])
            limit = config["limit"]
            period = config["period"]

            # Key for tracking requests
            key = f"{user_ip}:{endpoint}"

            # Initialize or update request count
            if key not in rate_limit_store:
                rate_limit_store[key] = {"count": 1, "start_time": current_time}
            else:
                elapsed_time = current_time - rate_limit_store[key]["start_time"]
                if elapsed_time < period:
                    rate_limit_store[key]["count"] += 1
                else:
                    rate_limit_store[key] = {"count": 1, "start_time": current_time}

            # Enforce rate limit
            if rate_limit_store[key]["count"] > limit:
                retry_after = period - elapsed_time
                return jsonify({
                    "error": "Rate limit exceeded",
                    "retry_after": retry_after,
                }), 429

            return f(*args, **kwargs)

        return wrapper
    return decorator
