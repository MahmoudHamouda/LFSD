from flask import Blueprint, request, jsonify
from db import get_db_session
from models import Notification

notification_blueprint = Blueprint("notification_service", __name__)


# GET /notifications
@notification_blueprint.route("/", methods=["GET"])
def get_notifications():
    user_id = request.args.get("user_id")
    if not user_id:
         return jsonify({"error": "user_id is required"}), 400

    session = get_db_session()
    # Sort by created_at desc
    notifications = (
        session.query(Notification).filter_by(user_id=user_id).order_by(Notification.created_at.desc()).all()
    )
    session.close()

    notification_list = [
        {
            "notification_id": n.notification_id,
            "user_id": n.user_id,
            "message": n.message,
            "type": n.type,
            "metadata": n.meta_data,
            "read_status": n.read_status,
            "created_at": n.created_at,
            "updated_at": n.updated_at,
        }
        for n in notifications
    ]

    return jsonify({"status": "success", "data": notification_list}), 200

# POST /notifications/read
@notification_blueprint.route("/read", methods=["POST"])
def mark_notifications_read():
    data = request.json
    user_id = data.get("user_id")
    notification_ids = data.get("notification_ids") # Expect list of IDs

    if not user_id or not notification_ids:
        return jsonify({"error": "user_id and notification_ids list required"}), 400
    
    if not isinstance(notification_ids, list):
         return jsonify({"error": "notification_ids must be a list"}), 400

    session = get_db_session()
    # Batch update
    updated_count = session.query(Notification).filter(
        Notification.user_id == user_id,
        Notification.notification_id.in_(notification_ids)
    ).update({Notification.read_status: True}, synchronize_session=False)
    
    session.commit()
    
    if updated_count > 0:
        _emit_activity_feed(user_id, "NOTIFICATIONS_READ", {"count": updated_count, "ids": notification_ids})
        # Determine if we log each one or a batch. Batch log for audit.
        _emit_audit_log("notifications", "batch", "UPDATE", str(user_id), {"read_status": True, "ids": notification_ids})

    session.close()

    return jsonify({"status": "success", "updated_count": updated_count}), 200

# Old route support for backward compatibility if needed, map to new logic? 
# or just keep as is? The plan said "refactor", but maybe keeping the old ID-based route is safer if other agents rely on it.
# I will leave the old ID-based GET route as deprecated alias if I can, or just replace it. A clean break is "contract first" so I'll replace.
# But wait, original code had: @notification_blueprint.route("/<int:user_id>"...
# My new code is @notification_blueprint.route("/", ... that expects query param ?user_id=...
# This aligns with standard REST for collections.

# POST /notifications/<user_id> (Create - usually internal)
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
        user_id=user_id, message=message, type=type, meta_data=metadata
    )
    session.add(new_notification)
    session.commit()
    
    _emit_activity_feed(user_id, "NOTIFICATION_CREATED", {"message": message, "type": type})

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


# PUT /notifications/<user_id>/<notification_id> (Update single)
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

    old_status = notification.read_status
    notification.read_status = read_status
    session.commit()
    
    if old_status != read_status:
         _emit_activity_feed(user_id, "NOTIFICATION_UPDATED", {"id": notification_id, "read": read_status})

    session.close()

    return (
        jsonify({"status": "success", "message": "Notification updated"}),
        200,
    )

# Event helper functions
def _emit_activity_feed(user_id, action_type, details):
    try:
        from services.activity_feed_service.models import ActivityFeed
        from db import get_db_session
        s = get_db_session()
        feed = ActivityFeed(user_id=user_id, action_type=action_type, details=details)
        s.add(feed)
        s.commit()
        s.close()
    except Exception as e:
        print(f"Failed to emit activity feed: {e}")

def _emit_audit_log(table, record_id, action, performed_by, changed_data=None):
    try:
        from services.audit_log_service.models import AuditLog
        from db import get_db_session
        s = get_db_session()
        log = AuditLog(
            table_name=table,
            record_id=record_id, 
            action=action, 
            performed_by=performed_by,
            changed_data=changed_data
        )
        s.add(log)
        s.commit()
        s.close()
    except Exception as e:
        print(f"Failed to emit audit log: {e}")
