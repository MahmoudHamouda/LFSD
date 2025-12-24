from flask import Blueprint, request, jsonify
from services.chat_service.db.feedback_repository import FeedbackRepository

recommendation_feedback_controller = Blueprint(
    "recommendation_feedback_controller", __name__
)


@recommendation_feedback_controller.route(
    "/recommendation_feedback", methods=["POST"]
)
def submit_recommendation_feedback():
    data = request.json
    FeedbackRepository.save_feedback(data)
    return jsonify({"message": "Recommendation feedback submitted"}), 201
