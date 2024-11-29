```python
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class Recommendation(Base):
    __tablename__ = "recommendations"

    recommendation_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    type = Column(String(50))  # e.g., "lifestyle", "financial"
    context = Column(String(255), nullable=True)
    content = Column(JSON, nullable=False)  # Recommendation details
    created_at = Column(DateTime, default=datetime.datetime.utcnow)