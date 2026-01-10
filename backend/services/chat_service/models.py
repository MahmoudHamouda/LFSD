from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    Boolean,
)
from models.database import Base
import datetime


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    session_id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    context = Column(String(255), nullable=True)
    title = Column(String(255), nullable=True)
    mode = Column(String(50), default="advisory")  # 'advisory' or 'support'


class ChatHistory(Base):
    __tablename__ = "chat_history"

    message_id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.session_id"))
    user_id = Column(String, ForeignKey("users.id"))
    message_type = Column(String(50))  # "user" or "assistant"
    content = Column(String(1000))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    is_summarized = Column(Boolean, default=False)

    # Token Tracking (Growth Agent)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    model_used = Column(String(100), nullable=True)


class ChatSummary(Base):
    __tablename__ = "chat_summaries"

    summary_id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.session_id"))
    summary_content = Column(String(2000))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(
        String(50), nullable=False
    )  # Message ID for which feedback is provided
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    feedback = Column(String(500), nullable=False)  # Feedback content
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
