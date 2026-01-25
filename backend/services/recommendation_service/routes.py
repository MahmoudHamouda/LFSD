from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from .db import db_session
from .models import Recommendation
import logging
from typing import Optional

logger = logging.getLogger(__name__)

recommendation_blueprint = Blueprint("recommendation_service", __name__)

# --- Configuration & Auth (Mock/Placeholder) ---
MAX_PAGE_SIZE = 100

def _validate_user_access(target_user_id: str):
    """
    Placeholder for authentication and ownership check.
    In production, this would verify JWT claims against target_user_id.
    """
    # current_user_id = auth_provider.get_user_id()
    # if current_user_id != target_user_id:
    #     raise PermissionError("Unauthorized access to user recommendations")
    logger.warning("Auth placeholder used - validation skipped.")

# --- Endpoints ---

@recommendation_blueprint.route("/<string:user_id>", methods=["GET"])
def get_recommendations(user_id: str):
    """
    Fetch recommendations for a specific user with pagination and deterministic ordering.
    """
    try:
        _validate_user_access(user_id)
        
        # Pagination
        try:
            limit = min(int(request.args.get("limit", 20)), MAX_PAGE_SIZE)
            offset = max(int(request.args.get("offset", 0)), 0)
        except ValueError:
            return jsonify({"error": "Invalid pagination parameters"}), 400

        with db_session() as session:
            # Deterministic ordering by created_at DESC
            recommendations = session.query(Recommendation).filter(
                Recommendation.user_id == user_id
            ).order_by(Recommendation.created_at.desc()).offset(offset).limit(limit).all()
            
            recommendation_list = [
                {
                    "recommendation_id": r.recommendation_id,
                    "user_id": r.user_id,
                    "type": r.type,
                    "context": r.context,
                    "content": r.content,
                    "created_at": r.created_at.isoformat()
                }
                for r in recommendations
            ]
            
            return jsonify({
                "status": "success", 
                "data": recommendation_list,
                "meta": {"limit": limit, "offset": offset, "count": len(recommendation_list)}
            }), 200
            
    except PermissionError as e:
        return jsonify({"error": str(e)}), 403
    except Exception as e:
        logger.error(f"Error fetching recommendations for user {user_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500

@recommendation_blueprint.route("/<string:user_id>", methods=["POST"])
def create_recommendation(user_id: str):
    """
    Create a new recommendation. 
    Includes idempotency check, payload validation, and transaction safety.
    """
    _validate_user_access(user_id)
    
    data = request.get_json(silent=True) or {}
    
    # 1. Validation & Sanitization
    rec_type = data.get("type", "").strip()
    context = data.get("context")
    content = data.get("content")
    idempotency_key = data.get("idempotency_key") # Optional but recommended

    if not rec_type or not context or not content:
        return jsonify({"error": "Type, context, and content are required"}), 400
    
    # Sanity checks on size
    if len(str(context)) > 1000 or len(str(content)) > 10000:
        return jsonify({"error": "Payload exceeds safety limits"}), 413

    try:
        with db_session() as session:
            # 2. Idempotency Check (Basic)
            # If the user is submitting the exact same content within a short window, or using a key
            if idempotency_key:
                existing = session.query(Recommendation).filter(
                    Recommendation.user_id == user_id,
                    Recommendation.context == f"idempotent:{idempotency_key}" # Hacky proxy
                ).first()
                if existing:
                    return jsonify({"status": "success", "recommendation_id": existing.recommendation_id, "note": "Duplicate suppressed"}), 200

            # 3. Create Recommendation
            new_recommendation = Recommendation(
                user_id=user_id,
                type=rec_type,
                context=context if not idempotency_key else f"idempotent:{idempotency_key}",
                content=content
            )
            
            # AI calls should ideally happen outside this WITH block if they take long,
            # but for consistency with the request, ensure DB write happens AFTER any logic.
            # In this structure, content is passed IN, so no external call happens here.
            
            session.add(new_recommendation)
            session.flush() # Generate UUID before commit
            
            rec_id = new_recommendation.recommendation_id
            
            return jsonify({
                "status": "success",
                "recommendation_id": rec_id,
                "content": content
            }), 201
            
    except Exception as e:
        logger.error(f"Error creating recommendation for user {user_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500

@recommendation_blueprint.route("/details/<string:recommendation_id>", methods=["GET"])
def get_recommendation_details(recommendation_id: str):
    """
    Get detailed view of a single recommendation.
    """
    try:
        with db_session() as session:
            recommendation = session.query(Recommendation).filter(
                Recommendation.recommendation_id == recommendation_id
            ).first()

            if not recommendation:
                return jsonify({"error": "Recommendation not found"}), 404
            
            # _validate_user_access(recommendation.user_id)

            return jsonify({
                "recommendation_id": recommendation.recommendation_id,
                "user_id": recommendation.user_id,
                "type": recommendation.type,
                "context": recommendation.context,
                "content": recommendation.content,
                "created_at": recommendation.created_at.isoformat()
            }), 200
            
    except Exception as e:
        logger.error(f"Error fetching recommendation {recommendation_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500
