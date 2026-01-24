from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from .db import db_session
from .models import User
import logging

logger = logging.getLogger(__name__)

# Blueprint for user-related routes
user_blueprint = Blueprint("user_service", __name__)

ALLOWED_UPDATE_FIELDS = {"first_name", "last_name", "phone_number", "preferences", "gender", "date_of_birth"}

def _bad_request(msg: str):
    return jsonify({"error": msg}), 400

@user_blueprint.route("/<string:user_id>", methods=["GET"])
def get_user(user_id: str):
    """Retrieve an active user profile."""
    try:
        with db_session() as session:
            user = session.query(User).filter(
                User.user_id == user_id,
                User.is_deleted == False
            ).first()
            
            if not user:
                return jsonify({"error": "User not found or deactivated"}), 404

            return jsonify({
                "user_id": user.user_id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "phone_number": user.phone_number,
                "gender": user.gender,
                "status": user.status,
                "preferences": user.preferences,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "updated_at": user.updated_at.isoformat() if user.updated_at else None
            }), 200
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500

@user_blueprint.route("/", methods=["POST"])
def create_user():
    """Register a new user profile."""
    data = request.get_json(silent=True) or {}
    
    # 1. Validation
    for f in ("first_name", "last_name", "email"):
        if not data.get(f):
            return _bad_request(f"Missing required field: {f}")

    email = str(data["email"]).strip().lower()
    
    # 2. Preferences check
    prefs = data.get("preferences", {})
    if prefs is not None and not isinstance(prefs, dict):
        return _bad_request("preferences must be a JSON object")

    try:
        with db_session() as session:
            # 3. Check for existing email (integrity)
            existing = session.query(User).filter(User.email == email).first()
            if existing:
                if existing.is_deleted:
                    # Option: Reactivate or Fail. For now, fail to prevent hijacking.
                    return jsonify({"error": "Account recently deactivated. Please contact support."}), 409
                return jsonify({"error": "A user with this email already exists"}), 409

            new_user = User(
                first_name=str(data["first_name"]).strip(),
                last_name=str(data["last_name"]).strip(),
                email=email,
                phone_number=data.get("phone_number"),
                gender=data.get("gender"),
                preferences=prefs or {}
            )
            
            session.add(new_user)
            session.flush() 
            assigned_id = new_user.user_id
            
            return jsonify({
                "status": "success",
                "message": "User created successfully", 
                "user_id": assigned_id
            }), 201

    except IntegrityError:
        return jsonify({"error": "User creation failed: Data integrity violation"}), 409
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return jsonify({"error": "Internal server error"}), 500

@user_blueprint.route("/<string:user_id>", methods=["PUT"])
def update_user(user_id: str):
    """Update user profile with mass-assignment protection."""
    data = request.get_json(silent=True) or {}

    updates = {k: v for k, v in data.items() if k in ALLOWED_UPDATE_FIELDS}
    if not updates:
        return _bad_request(f"No valid fields provided. Allowed: {sorted(list(ALLOWED_UPDATE_FIELDS))}")

    try:
        with db_session() as session:
            user = session.query(User).filter(
                User.user_id == user_id,
                User.is_deleted == False
            ).first()
            
            if not user:
                return jsonify({"error": "User not found"}), 404

            for key, value in updates.items():
                setattr(user, key, value)

            return jsonify({"status": "success", "message": "User updated successfully"}), 200

    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500

@user_blueprint.route("/<string:user_id>", methods=["DELETE"])
def delete_user(user_id: str):
    """Perform a secure soft-delete of a user."""
    try:
        from sqlalchemy import func
        with db_session() as session:
            user = session.query(User).filter(
                User.user_id == user_id,
                User.is_deleted == False
            ).first()
            
            if not user:
                return jsonify({"error": "User not found"}), 404

            user.is_deleted = True
            user.deleted_at = func.now()
            user.status = "INACTIVE"
            
            return jsonify({"status": "success", "message": "User deactivated successfully"}), 200

    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500
