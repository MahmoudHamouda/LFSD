from flask import Blueprint, request, jsonify
from db import get_db_connection
import datetime

activity_feed_blueprint = Blueprint("activity_feed_service", __name__)


# GET /users/{user_id}/activity-feed
@activity_feed_blueprint.route(
    "/users/<int:user_id>/activity-feed", methods=["GET"]
)
def get_activity_feed(user_id):
    action_type = request.args.get("action_type")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    query = "SELECT * FROM ActivityFeed WHERE user_id = %s"
    params = [user_id]

    if action_type:
        query += " AND action_type = %s"
        params.append(action_type)

    if start_date and end_date:
        query += " AND created_at BETWEEN %s AND %s"
        params.extend([start_date, end_date])

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, tuple(params))
    activities = cursor.fetchall()
    conn.close()

    activity_list = [
        {
            "activity_id": a[0],
            "user_id": a[1],
            "action_type": a[2],
            "details": a[3],
            "created_at": a[4],
        }
        for a in activities
    ]

    return jsonify({"status": "success", "data": activity_list}), 200


# POST /users/{user_id}/activity-feed
@activity_feed_blueprint.route(
    "/users/<int:user_id>/activity-feed", methods=["POST"]
)
def create_activity_feed_entry(user_id):
    data = request.json
    action_type = data.get("action_type")
    details = data.get("details")

    if not action_type or not details:
        return jsonify({"error": "action_type and details are required."}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO ActivityFeed (user_id, action_type, details, created_at)
        VALUES (%s, %s, %s, %s) RETURNING activity_id
        """,
        (user_id, action_type, str(details), datetime.datetime.utcnow()),
    )
    activity_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "activity_id": activity_id}), 201
