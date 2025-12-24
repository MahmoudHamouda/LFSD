from flask import Blueprint, request, jsonify
from middleware.authentication import require_authentication
from shared.logging import log_event
from shared.db_connection import get_db_connection
import datetime

partner_blueprint = Blueprint("partner_service", __name__)


# POST /partners/onboard
@partner_blueprint.route("/partners/onboard", methods=["POST"])
@require_authentication
def onboard_partner():
    data = request.json
    required_fields = [
        "partner_name",
        "contact_person",
        "email",
        "service_type",
        "api_endpoint",
        "user_id",
    ]

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    # Validate user_id
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id FROM Users WHERE user_id = %s", (data["user_id"],)
    )
    user = cursor.fetchone()
    if not user:
        conn.close()
        return jsonify({"error": "Invalid user_id."}), 400

    cursor.execute(
        """
        INSERT INTO Partners (partner_name, contact_person, email, phone, service_type, 
                              service_description, website_url, api_endpoint, user_id, status, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING partner_id
        """,
        (
            data["partner_name"],
            data["contact_person"],
            data["email"],
            data.get("phone"),
            data["service_type"],
            data.get("service_description", ""),
            data.get("website_url"),
            data["api_endpoint"],
            data["user_id"],
            "Pending Approval",
            datetime.datetime.utcnow(),
        ),
    )
    partner_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()

    log_event("Partner onboarded successfully", level="INFO")
    return (
        jsonify(
            {
                "status": "success",
                "partner_id": partner_id,
                "message": "Partner onboarded successfully and pending approval.",
            }
        ),
        201,
    )


# GET /partners
@partner_blueprint.route("/partners", methods=["GET"])
@require_authentication
def get_all_partners():
    status_filter = request.args.get("status")
    user_id_filter = request.args.get("user_id")
    query = "SELECT partner_id, partner_name, status FROM Partners"
    params = []

    if status_filter or user_id_filter:
        query += " WHERE"
        conditions = []
        if status_filter:
            conditions.append("status = %s")
            params.append(status_filter)
        if user_id_filter:
            conditions.append("user_id = %s")
            params.append(user_id_filter)
        query += " AND ".join(conditions)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    partners = cursor.fetchall()
    conn.close()

    partner_list = [
        {"partner_id": p[0], "partner_name": p[1], "status": p[2]}
        for p in partners
    ]

    log_event("Retrieved all partners", level="INFO")
    return jsonify({"status": "success", "data": partner_list}), 200


# GET /partners/{partner_id}
@partner_blueprint.route("/partners/<int:partner_id>", methods=["GET"])
@require_authentication
def get_partner_details(partner_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM Partners WHERE partner_id = %s", (partner_id,)
    )
    partner = cursor.fetchone()
    conn.close()

    if not partner:
        return jsonify({"error": "Partner not found"}), 404

    partner_details = {
        "partner_id": partner[0],
        "partner_name": partner[1],
        "contact_person": partner[2],
        "email": partner[3],
        "phone": partner[4],
        "service_type": partner[5],
        "service_description": partner[6],
        "website_url": partner[7],
        "api_endpoint": partner[8],
        "user_id": partner[9],
        "status": partner[10],
        "created_at": partner[11],
    }

    log_event(f"Retrieved details for partner_id: {partner_id}", level="INFO")
    return jsonify({"status": "success", "data": partner_details}), 200


# PUT /partners/{partner_id}/approve
@partner_blueprint.route("/partners/<int:partner_id>/approve", methods=["PUT"])
@require_authentication
def approve_partner(partner_id):
    data = request.json
    action = data.get("action")  # "approve" or "reject"
    reason = data.get("reason", "")

    if action not in ["approve", "reject"]:
        return (
            jsonify(
                {"error": "Invalid action. Must be 'approve' or 'reject'."}
            ),
            400,
        )

    status = "Approved" if action == "approve" else "Rejected"
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE Partners SET status = %s, updated_at = %s WHERE partner_id = %s",
        (status, datetime.datetime.utcnow(), partner_id),
    )
    conn.commit()
    conn.close()

    message = f"Partner {status.lower()} successfully."
    log_event(
        f"Partner {partner_id} {status.lower()} successfully", level="INFO"
    )
    return jsonify({"status": "success", "message": message}), 200


# POST /partners/<int:partner_id>/orders
@partner_blueprint.route("/partners/<int:partner_id>/orders", methods=["POST"])
@require_authentication
def create_order(partner_id):
    data = request.json
    required_fields = ["user_id", "type", "status", "total_amount"]

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    # Validate user_id
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id FROM Users WHERE user_id = %s", (data["user_id"],)
    )
    user = cursor.fetchone()
    if not user:
        conn.close()
        return jsonify({"error": "Invalid user_id."}), 400

    cursor.execute(
        """
        INSERT INTO Orders (user_id, provider_id, type, status, pickup_location, dropoff_location, 
                           delivery_location, reservation_details, total_amount, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING order_id
        """,
        (
            data["user_id"],
            partner_id,
            data["type"],
            data["status"],
            data.get("pickup_location"),
            data.get("dropoff_location"),
            data.get("delivery_location"),
            data.get("reservation_details"),
            data["total_amount"],
            datetime.datetime.utcnow(),
        ),
    )
    order_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()

    log_event(
        f"Order created successfully for partner_id: {partner_id}",
        level="INFO",
    )
    return (
        jsonify(
            {
                "status": "success",
                "order_id": order_id,
                "message": "Order created successfully.",
            }
        ),
        201,
    )


# POST /auth/logout
@partner_blueprint.route("/auth/logout", methods=["POST"])
@require_authentication
def logout():
    data = request.json
    required_fields = ["user_id", "token"]

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO TokenBlacklist (user_id, token, blacklisted_at, expiry_date)
        VALUES (%s, %s, %s, %s)
        """,
        (
            data["user_id"],
            data["token"],
            datetime.datetime.utcnow(),
            data.get(
                "expiry_date",
                datetime.datetime.utcnow() + datetime.timedelta(hours=1),
            ),
        ),
    )
    conn.commit()
    conn.close()

    log_event(
        f"User {data['user_id']} logged out successfully and token blacklisted",
        level="INFO",
    )
    return (
        jsonify(
            {
                "status": "success",
                "message": "User logged out successfully and token blacklisted.",
            }
        ),
        200,
    )
