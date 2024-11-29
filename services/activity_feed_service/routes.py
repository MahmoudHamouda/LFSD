```python
from flask import Blueprint, request, jsonify
from db import get_db_session
from models import ActivityFeed

activity_feed_blueprint = Blueprint("activity_feed_service", __name__)

# GET /activity-feed/<user_id>
@activity_feed_blueprint.route("/<int:user_id>", methods=["GET"])
def get_activity_feed(user_id):
    action_type = request.args.get("action_type")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    session = get_db_session()
    query = session.query(ActivityFeed).filter_by(user_id=user_id)

    if action_type:
        query = query.filter(ActivityFeed.action_type == action_type)
    if start_date and end_date:
        query = query.filter(ActivityFeed.timestamp.between(start_date, end_date))

    activities = query.all()
    session.close()

    activity_list = [
        {
            "activity_id": a.activity_id,
            "user_id": a.user_id,
            "action_type": a.action_type,
            "details": a.details,
            "timestamp": a.timestamp
        }
        for a in activities
    ]

    return jsonify({"status": "success", "data": activity_list}), 200

# POST /activity-feed/<user_id>
@activity_feed_blueprint.route("/<int:user_id>", methods=["POST"])
def create_activity_feed_entry(user_id):
    data = request.json
    action_type = data.get("action_type")
    details = data.get("details")

    if not action_type or not details:
        return jsonify({"error": "action_type and details are required"}), 400

    session = get_db_session()
    new_entry = ActivityFeed(user_id=user_id, action_type=action_type, details=details)
    session.add(new_entry)
    session.commit()
    session.close()

    return jsonify({"status": "success", "activity_id": new_entry.activity_id}), 201