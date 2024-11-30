from flask import Blueprint, request, jsonify
from db import get_db_session
from models import Partner

partner_blueprint = Blueprint("partner_service", __name__)


# GET /partners
@partner_blueprint.route("/", methods=["GET"])
def get_all_partners():
    session = get_db_session()
    partners = session.query(Partner).all()
    session.close()

    partner_list = [
        {
            "partner_id": p.partner_id,
            "name": p.name,
            "contact_email": p.contact_email,
            "phone_number": p.phone_number,
            "services_offered": p.services_offered,
        }
        for p in partners
    ]

    return jsonify({"status": "success", "data": partner_list}), 200


# POST /partners
@partner_blueprint.route("/", methods=["POST"])
def create_partner():
    data = request.json
    required_fields = ["name", "contact_email", "services_offered"]

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    session = get_db_session()
    new_partner = Partner(
        name=data["name"],
        contact_email=data["contact_email"],
        phone_number=data.get("phone_number"),
        services_offered=data["services_offered"],
    )
    session.add(new_partner)
    session.commit()
    session.close()

    return (
        jsonify({"status": "success", "partner_id": new_partner.partner_id}),
        201,
    )


# GET /partners/<partner_id>
@partner_blueprint.route("/<int:partner_id>", methods=["GET"])
def get_partner(partner_id):
    session = get_db_session()
    partner = session.query(Partner).filter_by(partner_id=partner_id).first()
    session.close()

    if not partner:
        return jsonify({"error": "Partner not found"}), 404

    return (
        jsonify(
            {
                "partner_id": partner.partner_id,
                "name": partner.name,
                "contact_email": partner.contact_email,
                "phone_number": partner.phone_number,
                "services_offered": partner.services_offered,
            }
        ),
        200,
    )


# PUT /partners/<partner_id>
@partner_blueprint.route("/<int:partner_id>", methods=["PUT"])
def update_partner(partner_id):
    data = request.json

    session = get_db_session()
    partner = session.query(Partner).filter_by(partner_id=partner_id).first()

    if not partner:
        session.close()
        return jsonify({"error": "Partner not found"}), 404

    for key, value in data.items():
        setattr(partner, key, value)

    session.commit()
    session.close()

    return (
        jsonify(
            {"status": "success", "message": "Partner updated successfully"}
        ),
        200,
    )


# DELETE /partners/<partner_id>
@partner_blueprint.route("/<int:partner_id>", methods=["DELETE"])
def delete_partner(partner_id):
    session = get_db_session()
    partner = session.query(Partner).filter_by(partner_id=partner_id).first()

    if not partner:
        session.close()
        return jsonify({"error": "Partner not found"}), 404

    session.delete(partner)
    session.commit()
    session.close()

    return (
        jsonify(
            {"status": "success", "message": "Partner deleted successfully"}
        ),
        200,
    )
