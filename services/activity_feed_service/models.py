```python
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class ActivityFeed(Base):
    __tablename__ = "activity_feed"

    activity_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    action_type = Column(String(50))  # e.g., "transaction", "recommendation"
    details = Column(JSON, nullable=False)  # Action details
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)