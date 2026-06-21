"""
Chat Service Models

Provides database models for chat sessions, history, summaries, and feedback.
These models integrate with the main application's database via the centralized Base.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from models.database import Base
from datetime import datetime, timezone


class ChatSession(Base):
    """Represents a chat conversation session."""

    __tablename__ = "chat_sessions"

    session_id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users_v2.id"), index=True)
    start_time = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    end_time = Column(DateTime(timezone=True), nullable=True)
    context = Column(String(255), nullable=True)
    title = Column(String(255), nullable=True)
    mode = Column(String(50), default="advisory")  # 'advisory' or 'support'


class ChatHistory(Base):
    """Stores individual messages within a chat session."""

    __tablename__ = "chat_history"

    message_id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.session_id"), index=True)
    user_id = Column(String, ForeignKey("users_v2.id"))
    message_type = Column(String(50))  # "user" or "assistant"
    content = Column(String(1000))
    timestamp = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    is_summarized = Column(Boolean, default=False)

    # Token Tracking for usage analytics
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    model_used = Column(String(100), nullable=True)


class ChatSummary(Base):
    """Stores summarized versions of chat sessions."""

    __tablename__ = "chat_summaries"

    summary_id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.session_id"))
    summary_content = Column(String(2000))
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class Feedback(Base):
    """User feedback on chat interactions."""

    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(String(50), nullable=False)
    user_id = Column(String, ForeignKey("users_v2.id"), nullable=False, index=True)
    feedback = Column(String(500), nullable=False)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
