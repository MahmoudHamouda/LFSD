from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    session_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    context = Column(String(255), nullable=True)


class ChatHistory(Base):
    __tablename__ = "chat_history"

    message_id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.session_id"))
    user_id = Column(Integer, ForeignKey("users.user_id"))
    message_type = Column(String(50))  # "user" or "assistant"
    content = Column(String(1000))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    is_summarized = Column(Boolean, default=False)


class ChatSummary(Base):
    __tablename__ = "chat_summaries"

    summary_id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.session_id"))
    summary_content = Column(String(2000))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(String(50), nullable=False)  # Message ID for which feedback is provided
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    feedback = Column(String(500), nullable=False)  # Feedback content
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
