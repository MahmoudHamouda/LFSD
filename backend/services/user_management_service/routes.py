from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from .db import get_db_session
from .models import User
import logging

logger = logging.getLogger(__name__)

# Blueprint for user-related routes
user_blueprint = Blueprint("user_service", __name__)

ALLOWED_UPDATE_FIELDS = {"first_name", "last_name", "phone_number", "preferences", "gender", "date_of_birth"}

def _bad_request(msg: str):
    return jsonify({"error": msg}), 400

@user_blueprint.route("/<int:user_id>", methods=["GET"])
def get_user(user_id: int):
    session = get_db_session()
    try:
        user = session.query(User).filter(User.user_id == user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        # Standardize preferences return
        prefs = user.preferences
        if prefs is None:
            prefs = {}
        elif not isinstance(prefs, dict):
            # Handle legacy string storage if it exists
            try:
                import json
                prefs = json.loads(prefs)
            except:
                prefs = {}

        return jsonify({
            "user_id": user.user_id,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "phone_number": user.phone_number,
            "gender": user.gender,
            "preferences": prefs,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }), 200
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {e}")
        return jsonify({"error": "Failed to fetch user"}), 500
    finally:
        session.close()

@user_blueprint.route("/", methods=["POST"])
def create_user():
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

    session = get_db_session()
    try:
        # 3. Check for existing email (integrity)
        existing = session.query(User).filter(User.email == email).first()
        if existing:
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
        session.commit()
        session.refresh(new_user)
        
        assigned_id = new_user.user_id
        return jsonify({"message": "User created successfully", "user_id": assigned_id}), 201

    except IntegrityError:
        session.rollback()
        return jsonify({"error": "User creation failed: Data integrity violation"}), 409
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating user: {e}")
        return jsonify({"error": "Internal server error during user creation"}), 500
    finally:
        session.close()

@user_blueprint.route("/<int:user_id>", methods=["PUT"])
def update_user(user_id: int):
    data = request.get_json(silent=True) or {}

    # 1. Mass-Assignment Protection (Whitelist)
    updates = {k: v for k, v in data.items() if k in ALLOWED_UPDATE_FIELDS}
    if not updates:
        return _bad_request(f"No valid fields provided for update. Allowed: {sorted(list(ALLOWED_UPDATE_FIELDS))}")

    # 2. Validation
    if "preferences" in updates and updates["preferences"] is not None and not isinstance(updates["preferences"], dict):
        return _bad_request("preferences must be a JSON object")

    session = get_db_session()
    try:
        user = session.query(User).filter(User.user_id == user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        # 3. Apply updates
        for key, value in updates.items():
            setattr(user, key, value)

        session.commit()
        return jsonify({"message": "User updated successfully"}), 200

    except Exception as e:
        session.rollback()
        logger.error(f"Error updating user {user_id}: {e}")
        return jsonify({"error": "Internal server error during update"}), 500
    finally:
        session.close()

@user_blueprint.route("/<int:user_id>", methods=["DELETE"])
def delete_user(user_id: int):
    session = get_db_session()
    try:
        user = session.query(User).filter(User.user_id == user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        session.delete(user)
        session.commit()
        return jsonify({"message": "User deleted successfully"}), 200

    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting user {user_id}: {e}")
        return jsonify({"error": "Internal server error during deletion"}), 500
    finally:
        session.close()

