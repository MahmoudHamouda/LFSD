from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id = Column(Integer, primary_key=True)
    table_name = Column(String(50), nullable=False)
    record_id = Column(Integer, nullable=False)
    action = Column(String(50), nullable=False)  # e.g., "INSERT", "UPDATE", "DELETE"
    changed_data = Column(JSON, nullable=True)  # Details of the change
    performed_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)