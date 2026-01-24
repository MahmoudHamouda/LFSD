from flask import Blueprint, request, jsonify
from .db import get_db_session
from .models import Notification
from sqlalchemy.sql import func
import logging

logger = logging.getLogger(__name__)

notification_blueprint = Blueprint("notification_service", __name__)

@notification_blueprint.route("/", methods=["GET"])
def get_notifications():
    """
    List notifications for a user.
    Supported query params: user_id, limit, offset, read_status
    """
    user_id = request.args.get("user_id")
    if not user_id:
         return jsonify({"error": "user_id is required"}), 400

    limit = min(int(request.args.get("limit", 50)), 100)
    offset = int(request.args.get("offset", 0))
    read_status = request.args.get("read_status")

    try:
        with get_db_session() as session:
            query = session.query(Notification).filter(Notification.user_id == str(user_id))
            
            if read_status is not None:
                is_read = read_status.lower() == "true"
                query = query.filter(Notification.read_status == is_read)
                
            notifications = (
                query.order_by(Notification.created_at.desc())
                .limit(limit)
                .offset(offset)
                .all()
            )
            
            return jsonify({
                "status": "success", 
                "data": [n.to_dict() for n in notifications],
                "pagination": {"limit": limit, "offset": offset}
            }), 200
    except Exception as e:
        logger.error(f"Error fetching notifications for {user_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500

@notification_blueprint.route("/read", methods=["POST"])
def mark_notifications_read():
    """Batch marks notifications as read."""
    data = request.get_json(silent=True) or {}
    user_id = data.get("user_id")
    notification_ids = data.get("notification_ids")

    if not user_id or not notification_ids or not isinstance(notification_ids, list):
        return jsonify({"error": "user_id and notification_ids list required"}), 400
    
    try:
        with get_db_session() as session:
            # Batch update with explicit updated_at refresh
            updated_count = session.query(Notification).filter(
                Notification.user_id == str(user_id),
                Notification.notification_id.in_(notification_ids)
            ).update(
                {
                    Notification.read_status: True,
                    Notification.updated_at: func.now()
                }, 
                synchronize_session=False
            )
            
            logger.info(f"User {user_id} marked {updated_count} notifications as read.")
            return jsonify({"status": "success", "updated_count": updated_count}), 200

    except Exception as e:
        logger.error(f"Error marking notifications as read: {e}")
        return jsonify({"error": "Update failed"}), 500

@notification_blueprint.route("/<string:user_id>", methods=["POST"])
def create_notification(user_id):
    """Internal endpoint to create a notification."""
    data = request.get_json(silent=True) or {}
    message = data.get("message")
    n_type = data.get("type") # Use n_type to avoid shadowing
    metadata = data.get("metadata", {})

    if not message or not n_type:
        return jsonify({"error": "Message and type are required"}), 400

    try:
        with get_db_session() as session:
            new_notification = Notification(
                user_id=str(user_id), 
                message=message, 
                notification_type=n_type, 
                metadata=metadata
            )
            session.add(new_notification)
            session.flush() # Populate ID
            
            notification_data = new_notification.to_dict()
            return jsonify({
                "status": "success",
                "data": notification_data
            }), 201
    except Exception as e:
        logger.error(f"Error creating notification for {user_id}: {e}")
        return jsonify({"error": "Creation failed"}), 500

@notification_blueprint.route("/<string:user_id>/<string:notification_id>", methods=["PUT"])
def update_notification_status(user_id, notification_id):
    """Update a single notification status."""
    data = request.get_json(silent=True) or {}
    read_status = data.get("read_status")

    if read_status is None or not isinstance(read_status, bool):
        return jsonify({"error": "read_status (boolean) is required"}), 400

    try:
        with get_db_session() as session:
            notification = session.query(Notification).filter(
                Notification.user_id == str(user_id),
                Notification.notification_id == str(notification_id)
            ).first()

            if not notification:
                return jsonify({"error": "Notification not found"}), 404

            notification.read_status = read_status
            return jsonify({"status": "success", "message": "Notification updated"}), 200
            
    except Exception as e:
        logger.error(f"Error updating notification {notification_id}: {e}")
        return jsonify({"error": "Update failed"}), 500
