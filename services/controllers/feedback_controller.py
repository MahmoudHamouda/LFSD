from flask import Blueprint, request, jsonify
from services.chat_service.db.feedback_repository import FeedbackRepository
from services.chat_service.schemas.feedback_schema import FeedbackSchema

feedback_controller = Blueprint('feedback_controller', __name__)

@feedback_controller.route('/feedback', methods=['POST'])
def submit_feedback():
    data = request.json
    validated_data = FeedbackSchema().load(data)
    FeedbackRepository.save_feedback(validated_data)
    return jsonify({"message": "Feedback submitted successfully"}), 201

@feedback_controller.route('/feedback', methods=['GET'])
def get_feedback():
    feedback = FeedbackRepository.get_all_feedback()
    return jsonify({"feedback": [FeedbackSchema().dump(fb) for fb in feedback]}), 200
