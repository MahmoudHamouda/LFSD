from flask import Blueprint, request, jsonify
from sqlalchemy.exc import SQLAlchemyError
import logging
from ..db import db_session
from ..models import Recommendation, RecommendationFeedback

logger = logging.getLogger(__name__)

recommendation_feedback_controller = Blueprint(
    "recommendation_feedback_controller", __name__
)

def _validate_feedback_input(data):
    """Basic validation for feedback input."""
    if not isinstance(data, dict):
        return "Invalid input format"
    
    # Check for recommendation_id and user_id as minimum requirements
    if not data.get("recommendation_id"):
        return "Recommendation ID is required"
    if not data.get("user_id"):
        return "User ID is required"
    
    # Optional rating check
    rating = data.get("rating")
    if rating is not None:
        try:
            val = int(rating)
            if not (1 <= val <= 5):
                return "Rating must be between 1 and 5"
        except (ValueError, TypeError):
            return "Rating must be an integer"
            
    # Comment length check
    comment = data.get("comment")
    if comment and len(str(comment)) > 1000:
        return "Comment exceeds maximum length of 1000 characters"
        
    return None

@recommendation_feedback_controller.route(
    "/<string:recommendation_id>/feedback", methods=["POST"]
)
def submit_recommendation_feedback(recommendation_id: str):
    """
    Submit feedback for a specific recommendation.
    RESTful path: /recommendations/<id>/feedback
    """
    data = request.get_json(silent=True) or {}
    
    # Ensure recommendation_id in body matches path if provided, or inject path ID
    data["recommendation_id"] = recommendation_id
    
    validation_error = _validate_feedback_input(data)
    if validation_error:
        return jsonify({"error": validation_error}), 400

    try:
        with db_session() as session:
            # 1. Verify recommendation exists and belongs to the user (auth/ownership placeholder)
            rec = session.query(Recommendation).filter(
                Recommendation.recommendation_id == recommendation_id
            ).first()
            
            if not rec:
                return jsonify({"error": "Recommendation not found"}), 404
            
            # Simple ownership check placeholder
            if rec.user_id != data.get("user_id"):
                return jsonify({"error": "Unauthorized: user does not own this recommendation"}), 403

            # 2. Idempotency Check: Prevent duplicate feedback for same user/rec
            existing = session.query(RecommendationFeedback).filter(
                RecommendationFeedback.recommendation_id == recommendation_id,
                RecommendationFeedback.user_id == data.get("user_id")
            ).first()
            
            if existing:
                return jsonify({"error": "Feedback already submitted for this recommendation"}), 409

            # 3. Create feedback
            feedback = RecommendationFeedback(
                recommendation_id=recommendation_id,
                user_id=data.get("user_id"),
                rating=data.get("rating"),
                is_helpful=data.get("is_helpful"),
                comment=data.get("comment"),
                metadata_json=data.get("metadata")
            )
            
            session.add(feedback)
            session.flush() # Generate ID for logging/response
            
            logger.info(f"Feedback {feedback.id} recorded for recommendation {recommendation_id}")
            
            return jsonify({
                "status": "success",
                "feedback_id": feedback.id,
                "message": "Recommendation feedback submitted"
            }), 201

    except SQLAlchemyError as e:
        logger.error(f"Database error submitting feedback: {e}")
        return jsonify({"error": "Failed to save feedback to database"}), 500
    except Exception as e:
        logger.error(f"Unexpected error in feedback submission: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
