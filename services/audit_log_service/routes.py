from flask import Blueprint, request, jsonify
from db import get_db_session
from models import AuditLog

audit_log_blueprint = Blueprint("audit_log_service", __name__)

# GET /audit-logs
@audit_log_blueprint.route("/", methods=["GET"])
def get_audit_logs():
    table_name = request.args.get("table_name")
    action = request.args.get("action")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    session = get_db_session()
    query = session.query(AuditLog)

    if table_name:
        query = query.filter(AuditLog.table_name == table_name)
    if action:
        query = query.filter(AuditLog.action == action)
    if start_date and end_date:
        query = query.filter(AuditLog.timestamp.between(start_date, end_date))

    logs = query.all()
    session.close()

    log_list = [
        {
            "log_id": log.log_id,
            "table_name": log.table_name,
            "record_id": log.record_id,
            "action": log.action,
            "changed_data": log.changed_data,
            "performed_by": log.performed_by,
            "timestamp": log.timestamp
        }
        for log in logs
    ]

    return jsonify({"status": "success", "data": log_list}), 200

# POST /audit-logs
@audit_log_blueprint.route("/", methods=["POST"])
def create_audit_log():
    data = request.json
    table_name = data.get("table_name")
    record_id = data.get("record_id")
    action = data.get("action")
    changed_data = data.get("changed_data")
    performed_by = data.get("performed_by")

    if not all([table_name, record_id, action, performed_by]):
        return jsonify({"error": "All fields are required: table_name, record_id, action, performed_by"}), 400

    session = get_db_session()
    new_log = AuditLog(
        table_name=table_name,
        record_id=record_id,
        action=action,
        changed_data=changed_data,
        performed_by=performed_by
    )
    session.add(new_log)
    session.commit()
    session.close()

    return jsonify({"status": "success", "log_id": new_log.log_id}), 201