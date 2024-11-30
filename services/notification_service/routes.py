from flask import Blueprint, request, jsonify
from db import get_db_session
from models import Notification

notification_blueprint = Blueprint("notification_service", __name__)


# GET /notifications/<user_id>
@notification_blueprint.route("/<int:user_id>", methods=["GET"])
def get_notifications(user_id):
    session = get_db_session()
    notifications = (
        session.query(Notification).filter_by(user_id=user_id).all()
    )
    session.close()

    notification_list = [
        {
            "notification_id": n.notification_id,
            "user_id": n.user_id,
            "message": n.message,
            "type": n.type,
            "metadata": n.metadata,
            "read_status": n.read_status,
            "created_at": n.created_at,
            "updated_at": n.updated_at,
        }
        for n in notifications
    ]

    return jsonify({"status": "success", "data": notification_list}), 200


# POST /notifications/<user_id>
@notification_blueprint.route("/<int:user_id>", methods=["POST"])
def create_notification(user_id):
    data = request.json
    message = data.get("message")
    type = data.get("type")
    metadata = data.get("metadata", {})

    if not message or not type:
        return jsonify({"error": "Message and type are required"}), 400

    session = get_db_session()
    new_notification = Notification(
        user_id=user_id, message=message, type=type, metadata=metadata
    )
    session.add(new_notification)
    session.commit()
    session.close()

    return (
        jsonify(
            {
                "status": "success",
                "notification_id": new_notification.notification_id,
            }
        ),
        201,
    )


# PUT /notifications/<user_id>/<notification_id>
@notification_blueprint.route(
    "/<int:user_id>/<int:notification_id>", methods=["PUT"]
)
def update_notification(user_id, notification_id):
    data = request.json
    read_status = data.get("read_status")

    if read_status is None:
        return jsonify({"error": "read_status is required"}), 400

    session = get_db_session()
    notification = (
        session.query(Notification)
        .filter_by(user_id=user_id, notification_id=notification_id)
        .first()
    )

    if not notification:
        session.close()
        return jsonify({"error": "Notification not found"}), 404

    notification.read_status = read_status
    session.commit()
    session.close()

    return (
        jsonify({"status": "success", "message": "Notification updated"}),
        200,
    )
