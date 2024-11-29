from flask import Blueprint, request, jsonify
from db import get_db_session
from models import ChatSession, ChatHistory, ChatSummary
from openai_client import generate_response, summarize_chat

chat_blueprint = Blueprint("chat_service", __name__)

# POST /chat/start
@chat_blueprint.route("/start", methods=["POST"])
def start_chat():
    data = request.json
    user_id = data.get("user_id")
    context = data.get("context")

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    session = get_db_session()
    new_session = ChatSession(user_id=user_id, context=context)
    session.add(new_session)
    session.commit()
    session.close()

    return jsonify({"message": "Chat session started", "session_id": new_session.session_id}), 201

# POST /chat/<session_id>/message
@chat_blueprint.route("/<int:session_id>/message", methods=["POST"])
def handle_message(session_id):
    data = request.json
    user_id = data.get("user_id")
    message = data.get("message")

    if not user_id or not message:
        return jsonify({"error": "user_id and message are required"}), 400

    # Store the user message
    session = get_db_session()
    new_message = ChatHistory(session_id=session_id, user_id=user_id, message_type="user", content=message)
    session.add(new_message)
    session.commit()

    # Generate AI response
    ai_response = generate_response(message)
    new_response = ChatHistory(session_id=session_id, user_id=user_id, message_type="assistant", content=ai_response)
    session.add(new_response)
    session.commit()
    session.close()

    return jsonify({"user_message": message, "assistant_response": ai_response}), 200

# POST /chat/<session_id>/summarize
@chat_blueprint.route("/<int:session_id>/summarize", methods=["POST"])
def summarize_session(session_id):
    session = get_db_session()
    chat_history = session.query(ChatHistory).filter_by(session_id=session_id).all()

    if not chat_history:
        session.close()
        return jsonify({"error": "No chat history found for this session"}), 404

    messages = [entry.content for entry in chat_history if entry.message_type == "user"]
    summary = summarize_chat(messages)

    # Store the summary
    new_summary = ChatSummary(session_id=session_id, summary_content=summary)
    session.add(new_summary)
    session.commit()
    session.close()

    return jsonify({"summary": summary}), 201