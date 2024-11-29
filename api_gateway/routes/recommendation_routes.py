from flask import Blueprint, request, jsonify
from shared.db_connection import get_db_connection
from shared.openai_client import generate_recommendation
import datetime

recommendation_blueprint = Blueprint("recommendation_service", __name__)

# GET /users/{user_id}/recommendations
@recommendation_blueprint.route("/users/<int:user_id>/recommendations", methods=["GET"])
def get_recommendations(user_id):
    rec_type = request.args.get("type")

    query = "SELECT * FROM Recommendations WHERE user_id = %s"
    params = [user_id]

    if rec_type:
        query += " AND type = %s"
        params.append(rec_type)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, tuple(params))
    recommendations = cursor.fetchall()
    conn.close()

    recommendation_list = [
        {
            "recommendation_id": r[0],
            "user_id": r[1],
            "type": r[2],
            "source": r[3],
            "content": r[4],
            "created_at": r[5]
        }
        for r in recommendations
    ]

    return jsonify({"status": "success", "data": recommendation_list}), 200


# POST /users/{user_id}/recommendations
@recommendation_blueprint.route("/users/<int:user_id>/recommendations", methods=["POST"])
def create_recommendation(user_id):
    data = request.json
    context = data.get("context")
    preferences = data.get("preferences")

    if not context:
        return jsonify({"error": "Context is required"}), 400

    # Generate recommendation using OpenAI or custom logic
    recommendation_content = generate_recommendation(context, preferences)

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO Recommendations (user_id, type, source, content, created_at)
        VALUES (%s, %s, %s, %s, %s) RETURNING recommendation_id
        """,
        (user_id, "lifestyle", "context", recommendation_content, datetime.datetime.utcnow()),
    )
    recommendation_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()

    return jsonify({"status": "success", "recommendation_id": recommendation_id, "content": recommendation_content}), 201


# GET /recommendations/{recommendation_id}
@recommendation_blueprint.route("/recommendations/<int:recommendation_id>", methods=["GET"])
def get_recommendation(recommendation_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Recommendations WHERE recommendation_id = %s", (recommendation_id,))
    recommendation = cursor.fetchone()
    conn.close()

    if not recommendation:
        return jsonify({"error": "Recommendation not found"}), 404

    recommendation_details = {
        "recommendation_id": recommendation[0],
        "user_id": recommendation[1],
        "type": recommendation[2],
        "source": recommendation[3],
        "content": recommendation[4],
        "created_at": recommendation[5]
    }

    return jsonify({"status": "success", "data": recommendation_details}), 200
