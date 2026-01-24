"""
Partner Service Routes

Handles CRUD operations for integration partners (e.g., insurance providers, gym chains).
Refactored for security, validation, and architectural consistency.
"""

from flask import Blueprint, request, jsonify
from .db import get_db_session
from .models import Partner
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)

partner_blueprint = Blueprint("partner", __name__)

class PartnerLogic:
    """Encapsulates business logic for Partner management."""
    
    @staticmethod
    def validate_partner_data(data: dict, partial: bool = False) -> Optional[str]:
        """Simple validation for partner payloads."""
        required = ["name", "contact_email", "services_offered"]
        if not partial:
            for field in required:
                if field not in data or not data[field]:
                    return f"Missing required field: {field}"
        
        email = data.get("contact_email")
        if email and "@" not in email:
            return "Invalid email format"
            
        services = data.get("services_offered")
        if services is not None and not isinstance(services, list):
            return "services_offered must be a list"
            
        return None

@partner_blueprint.route("/", methods=["GET"])
def get_all_partners():
    """List all registered partners, excluding soft-deleted ones."""
    category = request.args.get("category")
    with get_db_session() as session:
        try:
            query = session.query(Partner).filter(Partner.is_deleted == False)
            if category:
                query = query.filter(Partner.category == category)
                
            partners = query.all()
            return jsonify({
                "status": "success",
                "data": [
                    {
                        "partner_id": p.partner_id,
                        "name": p.name,
                        "contact_email": p.contact_email,
                        "phone_number": p.phone_number,
                        "services_offered": p.services_offered,
                        "status": p.status,
                        "category": p.category,
                        "created_at": p.created_at.isoformat() if p.created_at else None
                    } for p in partners
                ]
            }), 200
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_all_partners: {e}")
            return jsonify({"error": "Internal database error"}), 500

@partner_blueprint.route("/", methods=["POST"])
def create_partner():
    """Register a new partner."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing request body"}), 400

    error = PartnerLogic.validate_partner_data(data)
    if error:
        return jsonify({"error": error}), 400

    with get_db_session() as session:
        try:
            new_partner = Partner(
                name=data["name"],
                contact_email=data["contact_email"],
                phone_number=data.get("phone_number"),
                services_offered=data["services_offered"]
            )
            session.add(new_partner)
            session.commit()
            return jsonify({
                "status": "success",
                "partner_id": new_partner.partner_id,
                "message": "Partner registered successfully"
            }), 201
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to create partner: {e}")
            return jsonify({"error": "Failed to create partner"}), 500

@partner_blueprint.route("/<int:partner_id>", methods=["GET"])
def get_partner(partner_id):
    """Retrieve a specific partner by ID."""
    with get_db_session() as session:
        partner = session.query(Partner).filter_by(partner_id=partner_id).first()
        if not partner:
            return jsonify({"error": "Partner not found"}), 404

        return jsonify({
            "partner_id": partner.partner_id,
            "name": partner.name,
            "contact_email": partner.contact_email,
            "phone_number": partner.phone_number,
            "services_offered": partner.services_offered
        }), 200

@partner_blueprint.route("/<int:partner_id>", methods=["PUT"])
def update_partner(partner_id):
    """Update partner details with mass-assignment protection."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    error = PartnerLogic.validate_partner_data(data, partial=True)
    if error:
        return jsonify({"error": error}), 400

    # Whitelist allowed fields to prevent mass-assignment vulnerabilities
    allowed_fields = {"name", "contact_email", "phone_number", "services_offered"}
    update_data = {k: v for k, v in data.items() if k in allowed_fields}

    with get_db_session() as session:
        try:
            partner = session.query(Partner).filter_by(partner_id=partner_id).first()
            if not partner:
                return jsonify({"error": "Partner not found"}), 404

            for key, value in update_data.items():
                setattr(partner, key, value)

            session.commit()
            return jsonify({"status": "success", "message": "Partner updated successfully"}), 200
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Update failed for partner {partner_id}: {e}")
            return jsonify({"error": "Update failed"}), 500

@partner_blueprint.route("/<int:partner_id>", methods=["DELETE"])
def delete_partner(partner_id):
    """Securely remove a partner via soft-delete."""
    with get_db_session() as session:
        try:
            partner = session.query(Partner).filter_by(partner_id=partner_id, is_deleted=False).first()
            if not partner:
                return jsonify({"error": "Partner not found"}), 404

            partner.is_deleted = True
            partner.deleted_at = func.now()
            partner.status = "INACTIVE"
            session.commit()
            return jsonify({"status": "success", "message": "Partner deactivated successfully"}), 200
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Deletion failed for partner {partner_id}: {e}")
            return jsonify({"error": "Deletion failed"}), 500
