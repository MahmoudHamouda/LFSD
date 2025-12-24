from flask import Blueprint, request, jsonify
from db import get_db_connection
import datetime

audit_blueprint = Blueprint("audit_service", __name__)


# GET /audit-logs
@audit_blueprint.route("/audit-logs", methods=["GET"])
def get_audit_logs():
    table_name = request.args.get("table_name")
    action = request.args.get("action")
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    query = "SELECT * FROM AuditLogs WHERE 1=1"
    params = []

    if table_name:
        query += " AND table_name = %s"
        params.append(table_name)

    if action:
        query += " AND action = %s"
        params.append(action)

    if start_date and end_date:
        query += " AND created_at BETWEEN %s AND %s"
        params.extend([start_date, end_date])

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, tuple(params))
    logs = cursor.fetchall()
    conn.close()

    log_list = [
        {
            "log_id": log[0],
            "table_name": log[1],
            "record_id": log[2],
            "action": log[3],
            "changed_data": log[4],
            "performed_by": log[5],
            "created_at": log[6],
        }
        for log in logs
    ]

    return jsonify({"status": "success", "data": log_list}), 200


# POST /audit-logs
@audit_blueprint.route("/audit-logs", methods=["POST"])
def create_audit_log():
    data = request.json
    table_name = data.get("table_name")
    record_id = data.get("record_id")
    action = data.get("action")
    changed_data = data.get("changed_data")
    performed_by = data.get("performed_by")

    if (
        not table_name
        or not record_id
        or not action
        or not changed_data
        or not performed_by
    ):
        return (
            jsonify(
                {
                    "error": "All fields are required: table_name, record_id, action, changed_data, performed_by"
                }
            ),
            400,
        )

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO AuditLogs (table_name, record_id, action, changed_data, performed_by, created_at)
        VALUES (%s, %s, %s, %s, %s, %s) RETURNING log_id
        """,
        (
            table_name,
            record_id,
            action,
            str(changed_data),
            performed_by,
            datetime.datetime.utcnow(),
        ),
    )
    log_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "log_id": log_id}), 201
