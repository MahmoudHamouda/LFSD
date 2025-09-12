import os, datetime, jwt
from functools import wraps
from flask import request, jsonify

SECRET_KEY = os.getenv("SECRET_KEY", "dev_insecure_key")


def validate_jwt(token: str):
    try:
        data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return {"valid": True, "data": data}
    except jwt.ExpiredSignatureError:
        return {"valid": False, "error": "expired"}
    except Exception:
        return {"valid": False, "error": "invalid"}


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization")
        if not auth or not auth.startswith("Bearer "):
            return jsonify({"status": "error", "message": "Token is missing"}), 401
        token = auth.split(" ", 1)[1].strip()
        res = validate_jwt(token)
        if not res["valid"]:
            return jsonify({"status": "error", "message": "Invalid or expired token"}), 401
        # Attach claims to request for downstream use
        request.jwt = res["data"]
        return f(*args, **kwargs)
    return decorated
