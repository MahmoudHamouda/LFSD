"""
Centralized Authentication & Authorization Utilities.

Provides both FastAPI and Flask-compatible authentication decorators,
consolidating all auth logic in one place. This replaces legacy_v1/shared/auth.py
"""

from functools import wraps
from typing import Optional
import jwt
from flask import request, jsonify
import core.config

# ============================================================================
# Flask-Compatible Decorators (for legacy Flask blueprints)
# ============================================================================


def validate_jwt_token(token: str) -> dict:
    """
    Validate a JWT token and return the decoded payload.

    Returns:
        dict with 'valid' boolean and either 'data' or 'error'
    """
    settings = core.config.get_settings()
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALG])
        return {"valid": True, "data": payload}
    except jwt.ExpiredSignatureError:
        return {"valid": False, "error": "Token has expired"}
    except jwt.InvalidTokenError:
        return {"valid": False, "error": "Invalid token"}
    except Exception as e:
        return {"valid": False, "error": str(e)}


def token_required(f):
    """
    Flask decorator to require a valid JWT token in the Authorization header.

    Usage:
        @app.route('/protected')
        @token_required
        def protected_route():
            user_id = request.jwt.get('user_id')
            return {'message': f'Hello {user_id}'}
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Missing or invalid Authorization header",
                    }
                ),
                401,
            )

        token = auth_header.split(" ", 1)[1].strip()
        validation_result = validate_jwt_token(token)

        if not validation_result["valid"]:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": validation_result.get(
                            "error", "Authentication failed"
                        ),
                    }
                ),
                401,
            )

        # Attach decoded JWT claims to request for downstream use
        request.jwt = validation_result["data"]
        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    """
    Flask decorator requiring admin role in JWT.
    Must be used AFTER @token_required.
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        jwt_data = getattr(request, "jwt", {})
        role = jwt_data.get("role", "user")

        if role != "admin":
            return (
                jsonify({"status": "error", "message": "Admin privileges required"}),
                403,
            )

        return f(*args, **kwargs)

    return decorated


# ============================================================================
# FastAPI Dependencies (already defined in core/authentication.py)
# ============================================================================
# from core.authentication import get_current_user, oauth2_scheme
# These are used with FastAPI's Depends() pattern
