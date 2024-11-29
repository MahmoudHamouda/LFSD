```python
from flask import Blueprint, request, jsonify
from db import get_db_session
from models import Recommendation
from openai_client import generate_recommendation

recommendation_blueprint = Blueprint("recommendation_service", __name__)

# GET /recommendations/<user_id>
@recommendation_blueprint.route("/<int:user_id>", methods=["GET"])
def get_recommendations(user_id):
    session = get_db_session()
    recommendations = session.query(Recommendation).filter_by(user_id=user_id).all()
    session.close()

    recommendation_list = [
        {
            "recommendation_id": r.recommendation_id,
            "user_id": r.user_id,
            "type": r.type,
            "context": r.context,
            "content": r.content,
            "created_at": r.created_at
        }
        for r in recommendations
    ]

    return jsonify({"status": "success", "data": recommendation_list}), 200

# POST /recommendations/<user_id>
@recommendation_blueprint.route("/<int:user_id>", methods=["POST"])
def create_recommendation(user_id):
    data = request.json
    recommendation_type = data.get("type")
    context = data.get("context")
    preferences = data.get("preferences")

    if not recommendation_type or not context:
        return jsonify({"error": "Type and context are required"}), 400

    # Generate recommendation using AI or custom logic
    recommendation_content = generate_recommendation(context, preferences)

    session = get_db_session()
    new_recommendation = Recommendation(
        user_id=user_id,
        type=recommendation_type,
        context=context,
        content=recommendation_content
    )
    session.add(new_recommendation)
    session.commit()
    session.close()

    return jsonify({
        "status": "success",
        "recommendation_id": new_recommendation.recommendation_id,
        "content": recommendation_content
    }), 201

# GET /recommendations/details/<recommendation_id>
@recommendation_blueprint.route("/details/<int:recommendation_id>", methods=["GET"])
def get_recommendation_details(recommendation_id):
    session = get_db_session()
    recommendation = session.query(Recommendation).filter_by(recommendation_id=recommendation_id).first()
    session.close()

    if not recommendation:
        return jsonify({"error": "Recommendation not found"}), 404

    return jsonify({
        "recommendation_id": recommendation.recommendation_id,
        "user_id": recommendation.user_id,
        "type": recommendation.type,
        "context": recommendation.context,
        "content": recommendation.content,
        "created_at": recommendation.created_at
    }), 200