from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from db import get_db_connection
import jwt
import datetime
from functools import wraps

user_blueprint = Blueprint("user_service", __name__)

SECRET_KEY = "your_secret_key"


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return (
                jsonify({"status": "error", "message": "Token is missing."}),
                401,
            )

        try:
            token = token.split()[1]  # Extract token from "Bearer <token>"
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        except:
            return (
                jsonify(
                    {"status": "error", "message": "Invalid or expired token."}
                ),
                401,
            )

        return f(*args, **kwargs)

    return decorated


# POST /auth/login
@user_blueprint.route("/auth/login", methods=["POST"])
def login_user():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Email and password are required",
                }
            ),
            400,
        )

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, password FROM Users WHERE email = %s", (email,)
    )
    user = cursor.fetchone()
    conn.close()

    if not user or not check_password_hash(user[1], password):
        return (
            jsonify({"status": "error", "message": "Invalid credentials"}),
            401,
        )

    token = jwt.encode(
        {
            "user_id": user[0],
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        },
        SECRET_KEY,
        algorithm="HS256",
    )
    return (
        jsonify(
            {
                "status": "success",
                "data": {"access_token": token, "expires_in": 3600},
            }
        ),
        200,
    )


# GET /auth/validate
@user_blueprint.route("/auth/validate", methods=["GET"])
@token_required
def validate_token():
    return jsonify({"status": "success", "message": "Token is valid."}), 200


# POST /users
@user_blueprint.route("/users", methods=["POST"])
def register_user():
    data = request.json
    required_fields = [
        "first_name",
        "last_name",
        "email",
        "password",
        "gender",
        "date_of_birth",
        "phone_number",
        "address",
    ]
    if not all(field in data for field in required_fields):
        return (
            jsonify({"status": "error", "message": "Missing required fields"}),
            400,
        )

    hashed_password = generate_password_hash(data["password"])
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO Users (first_name, last_name, email, password, gender, date_of_birth, phone_number, address, preferences, family_count, dependent_count, total_points, rank, friend_count, created_at, updated_at, social_account_id, social_provider, social_id, linked_at, last_active_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING user_id
        """,
        (
            data["first_name"],
            data["last_name"],
            data["email"],
            hashed_password,
            data["gender"],
            data["date_of_birth"],
            data["phone_number"],
            data["address"],
            data.get("preferences", "{}"),
            data.get("family_count", 0),
            data.get("dependent_count", 0),
            data.get("total_points", 0),
            data.get("rank", "New"),
            data.get("friend_count", 0),
            datetime.datetime.utcnow(),
            datetime.datetime.utcnow(),
            data.get("social_account_id"),
            data.get("social_provider"),
            data.get("social_id"),
            data.get("linked_at"),
            data.get("last_active_at", datetime.datetime.utcnow()),
        ),
    )
    user_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()

    return (
        jsonify(
            {
                "status": "success",
                "data": {
                    "user_id": user_id,
                    "created_at": datetime.datetime.utcnow(),
                },
            }
        ),
        201,
    )


# GET /users/{user_id}
@user_blueprint.route("/users/<int:user_id>", methods=["GET"])
@token_required
def get_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return jsonify({"status": "error", "message": "User not found"}), 404

    user_data = {
        "user_id": user[0],
        "first_name": user[1],
        "last_name": user[2],
        "email": user[3],
        "gender": user[4],
        "date_of_birth": user[5],
        "phone_number": user[6],
        "address": user[7],
        "preferences": user[8],
        "family_count": user[9],
        "dependent_count": user[10],
        "total_points": user[11],
        "rank": user[12],
        "friend_count": user[13],
        "created_at": user[14],
        "updated_at": user[15],
        "social_account_id": user[16],
        "social_provider": user[17],
        "social_id": user[18],
        "linked_at": user[19],
        "last_active_at": user[20],
    }
    return jsonify({"status": "success", "data": user_data}), 200


# PUT /users/{user_id}
@user_blueprint.route("/users/<int:user_id>", methods=["PUT"])
@token_required
def update_user(user_id):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE Users SET preferences = %s, family_count = %s, dependent_count = %s, total_points = %s, rank = %s, friend_count = %s, updated_at = %s, social_account_id = %s, social_provider = %s, social_id = %s, linked_at = %s, last_active_at = %s WHERE user_id = %s
        """,
        (
            data.get("preferences", "{}"),
            data.get("family_count", 0),
            data.get("dependent_count", 0),
            data.get("total_points", 0),
            data.get("rank", "New"),
            data.get("friend_count", 0),
            datetime.datetime.utcnow(),
            data.get("social_account_id"),
            data.get("social_provider"),
            data.get("social_id"),
            data.get("linked_at"),
            data.get("last_active_at", datetime.datetime.utcnow()),
            user_id,
        ),
    )
    conn.commit()
    conn.close()

    return (
        jsonify({"status": "success", "message": "User preferences updated"}),
        200,
    )


# DELETE /users/{user_id}
@user_blueprint.route("/users/<int:user_id>", methods=["DELETE"])
@token_required
def delete_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM Users WHERE user_id = %s", (user_id,))
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "message": "User deleted"}), 200


# GET /users/{user_id}/preferences
@user_blueprint.route("/users/<int:user_id>/preferences", methods=["GET"])
@token_required
def get_user_preferences(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT preferences FROM Users WHERE user_id = %s", (user_id,)
    )
    preferences = cursor.fetchone()
    conn.close()

    if not preferences:
        return (
            jsonify({"status": "error", "message": "Preferences not found"}),
            404,
        )

    return jsonify({"status": "success", "data": preferences[0]}), 200
