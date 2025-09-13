from flask import Blueprint, request, jsonify
from shared.db_connection import get_db_connection
import datetime

notification_blueprint = Blueprint("notification_service", __name__)


# GET /users/{user_id}/notifications
@notification_blueprint.route(
    "/users/<int:user_id>/notifications", methods=["GET"]
)
def get_notifications(user_id):
    read_status = request.args.get("read_status")
    start_date = request.args.get("start_date")

    query = "SELECT * FROM Notifications WHERE user_id = %s"
    params = [user_id]

    if read_status is not None:
        query += " AND read_status = %s"
        params.append(read_status.lower() == "true")

    if start_date:
        query += " AND created_at >= %s"
        params.append(start_date)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, tuple(params))
    notifications = cursor.fetchall()
    conn.close()

    notification_list = [
        {
            "notification_id": n[0],
            "user_id": n[1],
            "message": n[2],
            "read_status": n[3],
            "created_at": n[4],
            "updated_at": n[5],
        }
        for n in notifications
    ]

    return jsonify({"status": "success", "data": notification_list}), 200


# POST /users/{user_id}/notifications
@notification_blueprint.route(
    "/users/<int:user_id>/notifications", methods=["POST"]
)
def create_notification(user_id):
    data = request.json
    message = data.get("message")
    notification_type = data.get("type")
    metadata = data.get("metadata", {})

    if not message or not notification_type:
        return jsonify({"error": "Message and type are required."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO Notifications (user_id, message, type, metadata, read_status, created_at)
        VALUES (%s, %s, %s, %s, %s, %s) RETURNING notification_id
        """,
        (
            user_id,
            message,
            notification_type,
            str(metadata),
            False,
            datetime.datetime.utcnow(),
        ),
    )
    notification_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()

    return (
        jsonify({"status": "success", "notification_id": notification_id}),
        201,
    )


# PUT /users/{user_id}/notifications/{notification_id}
@notification_blueprint.route(
    "/users/<int:user_id>/notifications/<int:notification_id>", methods=["PUT"]
)
def update_notification(user_id, notification_id):
    data = request.json
    read_status = data.get("read_status")

    if read_status is None:
        return jsonify({"error": "read_status is required."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE Notifications SET read_status = %s, updated_at = %s
        WHERE user_id = %s AND notification_id = %s
        """,
        (read_status, datetime.datetime.utcnow(), user_id, notification_id),
    )
    conn.commit()
    conn.close()

    return (
        jsonify({"status": "success", "message": "Notification updated."}),
        200,
    )
