from flask import Blueprint, request, jsonify
from shared.utils import validate_jwt
import requests

feedback_bp = Blueprint('feedback', __name__)

@feedback_bp.route('/feedback', methods=['POST'])
@validate_jwt
def submit_feedback():
    feedback_data = request.json
    response = requests.post('http://chat_service/feedback', json=feedback_data)
    return jsonify(response.json()), response.status_code

@feedback_bp.route('/feedback', methods=['GET'])
@validate_jwt
def get_feedback():
    response = requests.get('http://chat_service/feedback')
    return jsonify(response.json()), response.status_code
