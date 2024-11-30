from flask import Blueprint, request, jsonify, redirect
from werkzeug.security import check_password_hash, generate_password_hash
from shared.db_connection import get_db_connection
from shared.config import (
    SECRET_KEY,
    OAUTH_CLIENT_ID,
    OAUTH_CLIENT_SECRET,
    OAUTH_REDIRECT_URI,
)
from shared.logging import logger
import jwt
import datetime
import requests
from urllib.parse import urlencode

authentication_blueprint = Blueprint("authentication_service", __name__)

# OAuth endpoints
OAUTH_PROVIDER_URL = "https://provider.com"


# POST /auth/register
@authentication_blueprint.route("/auth/register", methods=["POST"])
def register():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    first_name = data.get("first_name")
    last_name = data.get("last_name")

    if not email or not password or not first_name or not last_name:
        logger.error("Registration failed: Missing required fields")
        return jsonify({"error": "All fields are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM Users WHERE email = %s", (email,))
    if cursor.fetchone():
        conn.close()
        logger.error(f"Registration failed: Email {email} already registered")
        return jsonify({"error": "Email already registered"}), 400

    hashed_password = generate_password_hash(password)
    cursor.execute(
        "INSERT INTO Users (email, password, first_name, last_name, created_at) VALUES (%s, %s, %s, %s, %s)",
        (
            email,
            hashed_password,
            first_name,
            last_name,
            datetime.datetime.utcnow(),
        ),
    )
    conn.commit()
    conn.close()

    logger.info(f"User registered successfully: {email}")
    return (
        jsonify(
            {"status": "success", "message": "User registered successfully"}
        ),
        201,
    )


# POST /auth/login
@authentication_blueprint.route("/auth/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        logger.error("Login failed: Missing email or password")
        return jsonify({"error": "Email and password are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, password, account_status FROM Users WHERE email = %s",
        (email,),
    )
    user = cursor.fetchone()
    conn.close()

    if not user:
        logger.error(f"Login failed: Invalid credentials for {email}")
        return jsonify({"error": "Invalid credentials"}), 401

    if user[2] != "active":
        logger.error(f"Login failed: Account {email} is not active")
        return jsonify({"error": "Account is not active"}), 403

    if not check_password_hash(user[1], password):
        logger.error(f"Login failed: Invalid credentials for {email}")
        return jsonify({"error": "Invalid credentials"}), 401

    token = jwt.encode(
        {
            "user_id": user[0],
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        },
        SECRET_KEY,
        algorithm="HS256",
    )

    logger.info(f"User logged in successfully: {email}")
    return (
        jsonify(
            {"status": "success", "access_token": token, "expires_in": 3600}
        ),
        200,
    )


# GET /auth/oauth/login
@authentication_blueprint.route("/auth/oauth/login", methods=["GET"])
def oauth_login():
    params = {
        "client_id": OAUTH_CLIENT_ID,
        "redirect_uri": OAUTH_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid profile email",
    }
    oauth_url = f"{OAUTH_PROVIDER_URL}/authorize?{urlencode(params)}"
    return redirect(oauth_url)


# GET /auth/oauth/callback
@authentication_blueprint.route("/auth/oauth/callback", methods=["GET"])
def oauth_callback():
    code = request.args.get("code")
    if not code:
        logger.error("OAuth callback failed: Missing authorization code")
        return jsonify({"error": "Authorization code is required"}), 400

    # Exchange authorization code for access token
    token_url = f"{OAUTH_PROVIDER_URL}/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": OAUTH_REDIRECT_URI,
        "client_id": OAUTH_CLIENT_ID,
        "client_secret": OAUTH_CLIENT_SECRET,
    }

    token_response = requests.post(
        token_url, headers=headers, data=urlencode(data)
    )
    if token_response.status_code != 200:
        logger.error("OAuth callback failed: Failed to retrieve access token")
        return jsonify({"error": "Failed to retrieve access token"}), 400

    token_data = token_response.json()
    access_token = token_data.get("access_token")
    if not access_token:
        logger.error(
            "OAuth callback failed: Access token not found in response"
        )
        return jsonify({"error": "Access token not found"}), 400

    # Retrieve user information using access token
    user_info_url = f"{OAUTH_PROVIDER_URL}/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    user_info_response = requests.get(user_info_url, headers=headers)
    if user_info_response.status_code != 200:
        logger.error(
            "OAuth callback failed: Failed to retrieve user information"
        )
        return jsonify({"error": "Failed to retrieve user information"}), 400

    user_info = user_info_response.json()
    email = user_info.get("email")
    if not email:
        logger.error(
            "OAuth callback failed: Email not found in user information"
        )
        return jsonify({"error": "Email not found"}), 400

    # Check if user already exists, if not, register them
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM Users WHERE email = %s", (email,))
    user = cursor.fetchone()
    if not user:
        cursor.execute(
            "INSERT INTO Users (email, first_name, last_name, created_at) VALUES (%s, %s, %s, %s)",
            (
                email,
                user_info.get("given_name"),
                user_info.get("family_name"),
                datetime.datetime.utcnow(),
            ),
        )
        conn.commit()
        cursor.execute("SELECT user_id FROM Users WHERE email = %s", (email,))
        user = cursor.fetchone()
    conn.close()

    # Generate JWT token for the user
    token = jwt.encode(
        {
            "user_id": user[0],
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1),
        },
        SECRET_KEY,
        algorithm="HS256",
    )

    logger.info(f"User logged in via OAuth successfully: {email}")
    return (
        jsonify(
            {"status": "success", "access_token": token, "expires_in": 3600}
        ),
        200,
    )


# POST /auth/logout
@authentication_blueprint.route("/auth/logout", methods=["POST"])
def logout():
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        logger.error("Logout failed: Missing authorization token")
        return jsonify({"error": "Authorization token is required"}), 401

    try:
        decoded = jwt.decode(
            token.split(" ")[1], SECRET_KEY, algorithms=["HS256"]
        )
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO TokenBlacklist (user_id, token, blacklisted_at, expiry_date) VALUES (%s, %s, %s, %s)",
            (
                decoded["user_id"],
                token.split(" ")[1],
                datetime.datetime.utcnow(),
                decoded["exp"],
            ),
        )
        conn.commit()
        conn.close()
        logger.info(
            f"User logged out successfully: user_id {decoded['user_id']}"
        )
    except jwt.ExpiredSignatureError:
        logger.error("Logout failed: Token has expired")
        return jsonify({"error": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        logger.error("Logout failed: Invalid token")
        return jsonify({"error": "Invalid token"}), 401

    return (
        jsonify(
            {"status": "success", "message": "User logged out successfully"}
        ),
        200,
    )


# GET /auth/validate
@authentication_blueprint.route("/auth/validate", methods=["GET"])
def validate_token():
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        logger.error("Token validation failed: Missing authorization token")
        return jsonify({"error": "Authorization token is required"}), 401

    try:
        decoded = jwt.decode(
            token.split(" ")[1], SECRET_KEY, algorithms=["HS256"]
        )
        logger.info(
            f"Token validation successful: user_id {decoded['user_id']}"
        )
        return (
            jsonify(
                {
                    "status": "success",
                    "message": "Token is valid",
                    "user_id": decoded["user_id"],
                }
            ),
            200,
        )
    except jwt.ExpiredSignatureError:
        logger.error("Token validation failed: Token has expired")
        return jsonify({"error": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        logger.error("Token validation failed: Invalid token")
        return jsonify({"error": "Invalid token"}), 401
