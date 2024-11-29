Implements user-related endpoints.
```python
from flask import Blueprint, request, jsonify
from db import get_db_session
from models import User

user_blueprint = Blueprint("user_service", __name__)

# GET /users/<user_id>
@user_blueprint.route("/<int:user_id>", methods=["GET"])
def get_user(user_id):
    session = get_db_session()
    user = session.query(User).filter_by(user_id=user_id).first()
    session.close()

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "user_id": user.user_id,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "phone_number": user.phone_number,
        "preferences": user.preferences,
    }), 200

# POST /users
@user_blueprint.route("/", methods=["POST"])
def create_user():
    data = request.json
    required_fields = ["first_name", "last_name", "email"]

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    session = get_db_session()
    new_user = User(
        first_name=data["first_name"],
        last_name=data["last_name"],
        email=data["email"],
        phone_number=data.get("phone_number"),
        preferences=data.get("preferences", {}),
    )

    session.add(new_user)
    session.commit()
    session.close()

    return jsonify({"message": "User created successfully", "user_id": new_user.user_id}), 201

# PUT /users/<user_id>
@user_blueprint.route("/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    data = request.json

    session = get_db_session()
    user = session.query(User).filter_by(user_id=user_id).first()

    if not user:
        session.close()
        return jsonify({"error": "User not found"}), 404

    for key, value in data.items():
        setattr(user, key, value)

    session.commit()
    session.close()

    return jsonify({"message": "User updated successfully"}), 200

# DELETE /users/<user_id>
@user_blueprint.route("/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    session = get_db_session()
    user = session.query(User).filter_by(user_id=user_id).first()

    if not user:
        session.close()
        return jsonify({"error": "User not found"}), 404

    session.delete(user)
    session.commit()
    session.close()

    return jsonify({"message": "User deleted successfully"}), 200