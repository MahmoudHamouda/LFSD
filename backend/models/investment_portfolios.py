from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class InvestmentPortfolio(Base):
    """
    Tracks investment accounts and their performance.
    """
    __tablename__ = "investment_portfolios"

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    
    institution_name = Column(String, nullable=False) # IBKR, Robinhood
    portfolio_name = Column(String, nullable=True)
    
    total_value = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    
    daily_change_percent = Column(Float, nullable=True)
    total_return_percent = Column(Float, nullable=True)
    
    asset_allocation_json = Column(JSON, nullable=True) # {"stocks": 60, "bonds": 40}
    
    last_updated = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
