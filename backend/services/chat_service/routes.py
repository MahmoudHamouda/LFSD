from flask import Blueprint, request, jsonify
from db import get_db_session
from models import ChatSession, ChatHistory, ChatSummary
from openai_client import generate_response, summarize_chat, generate_title
import datetime

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
    # Default to advisory for generic start
    new_session = ChatSession(
        user_id=user_id, 
        context=context, 
        title="New Conversation", 
        mode="advisory"
    )
    session.add(new_session)
    session.commit()
    session_id = new_session.session_id
    session.close()

    return jsonify({
        "message": "Chat session started",
        "session_id": session_id
    }), 201

# POST /chat/<session_id>/message
@chat_blueprint.route("/<int:session_id>/message", methods=["POST"])
def handle_message(session_id):
    data = request.json
    user_id = data.get("user_id")
    message = data.get("message")

    if not user_id or not message:
        return jsonify({"error": "user_id and message are required"}), 400

    session = get_db_session()
    
    # 1. Fetch Chat Session
    chat_session = session.query(ChatSession).filter_by(session_id=session_id).first()
    if not chat_session:
        session.close()
        return jsonify({"error": "Chat session not found"}), 404

    # 2. Auto-titling for advisory chats
    if chat_session.mode == "advisory" and (not chat_session.title or chat_session.title == "New Conversation"):
         try:
             chat_session.title = generate_title(message)
         except Exception as e:
             print(f"Title generation error: {e}")

    # 3. Store the user message
    user_msg_entry = ChatHistory(
        session_id=session_id,
        user_id=user_id,
        message_type="user",
        content=message
    )
    session.add(user_msg_entry)
    session.commit()

    # 4. Generate AI response with usage
    ai_result = generate_response(message) # Now returns a dict
    ai_content = ai_result.get("content")
    usage = ai_result.get("usage", {})
    model = ai_result.get("model")

    # 5. Store AI response with usage tracking
    ai_msg_entry = ChatHistory(
        session_id=session_id,
        user_id=user_id,
        message_type="assistant",
        content=ai_content,
        input_tokens=usage.get("input_tokens"),
        output_tokens=usage.get("output_tokens"),
        model_used=model
    )
    session.add(ai_msg_entry)
    
    # 6. Emit usage event to activity feed
    _emit_activity_feed(user_id, "GEMINI_USAGE_RECORDED", {
        "session_id": session_id,
        "tokens": usage.get("total_tokens"),
        "model": model
    })
    
    session.commit()
    session.close()

    return jsonify({
        "user_message": message, 
        "assistant_response": ai_content,
        "usage": usage
    }), 200

# POST /chat/<session_id>/summarize
@chat_blueprint.route("/<int:session_id>/summarize", methods=["POST"])
def summarize_session(session_id):
    session = get_db_session()
    chat_history = session.query(ChatHistory).filter_by(session_id=session_id).all()

    if not chat_history:
        session.close()
        return jsonify({"error": "No chat history found for this session"}), 404

    # Filter user messages for summary context
    user_messages = [entry.content for entry in chat_history if entry.message_type == "user"]
    
    # Generate summary with usage
    summary_result = summarize_chat(user_messages)
    summary_content = summary_result.get("content")
    usage = summary_result.get("usage", {})
    
    # Store the summary
    new_summary = ChatSummary(session_id=session_id, summary_content=summary_content)
    session.add(new_summary)
    
    # Record usage if session has a user_id
    chat_session = session.query(ChatSession).filter_by(session_id=session_id).first()
    if chat_session:
        _emit_activity_feed(chat_session.user_id, "GEMINI_USAGE_RECORDED", {
            "session_id": session_id,
            "type": "summary",
            "tokens": usage.get("total_tokens")
        })

    session.commit()
    session.close()

    return jsonify({"summary": summary_content}), 201

# GET /chat/conversations
@chat_blueprint.route("/conversations", methods=["GET"])
def get_conversations():
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    session = get_db_session()
    sessions = session.query(ChatSession).filter_by(user_id=user_id).order_by(ChatSession.start_time.desc()).all()
    
    results = []
    for s in sessions:
        results.append({
            "session_id": s.session_id,
            "title": s.title or "New Conversation",
            "mode": s.mode,
            "start_time": s.start_time,
            "end_time": s.end_time
        })
    session.close()
    return jsonify({"status": "success", "data": results}), 200

# POST /support/chat
@chat_blueprint.route("/support", methods=["POST"])
def start_support_chat():
    data = request.json
    user_id = data.get("user_id")
    context = data.get("context")

    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    session = get_db_session()
    new_session = ChatSession(
        user_id=user_id, 
        context=context,
        mode="support",
        title=f"Support: {context}" if context else "Support Request"
    )
    session.add(new_session)
    session.commit()
    
    _emit_activity_feed(user_id, "SUPPORT_CHAT_STARTED", {"session_id": new_session.session_id, "context": context})
    _emit_audit_log("chat_sessions", str(new_session.session_id), "CREATE", str(user_id), {"mode": "support"})

    session_id = new_session.session_id
    session.close()

    return jsonify({
        "message": "Support chat started",
        "session_id": session_id
    }), 201

# Event helper functions
def _emit_activity_feed(user_id, action_type, details):
    try:
        from services.activity_feed_service.models import ActivityFeed
        from db import get_db_session
        s = get_db_session()
        feed = ActivityFeed(user_id=user_id, action_type=action_type, details=details)
        s.add(feed)
        s.commit()
        s.close()
    except Exception as e:
        print(f"Failed to emit activity feed: {e}")

def _emit_audit_log(table, record_id, action, performed_by, changed_data=None):
    try:
        from services.audit_log_service.models import AuditLog
        from db import get_db_session
        s = get_db_session()
        log = AuditLog(
            table_name=table,
            record_id=record_id, 
            action=action, 
            performed_by=performed_by,
            changed_data=changed_data
        )
        s.add(log)
        s.commit()
        s.close()
    except Exception as e:
        print(f"Failed to emit audit log: {e}")
