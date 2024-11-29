from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()

class Transaction(Base):
    __tablename__ = "transactions"

    transaction_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    amount = Column(Float, nullable=False)
    category = Column(String(50))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    description = Column(String(255))

class AffordabilityAnalysis(Base):
    __tablename__ = "affordability_analysis"

    analysis_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    item = Column(String(100))
    price = Column(Float, nullable=False)
    loan_term = Column(Integer, nullable=True)
    down_payment = Column(Float, nullable=True)
    monthly_payment = Column(Float, nullable=True)
    affordable = Column(String(10))  # "Yes" or "No"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class RecurringExpense(Base):
    __tablename__ = "recurring_expenses"

    expense_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    amount = Column(Float, nullable=False)
    category = Column(String(50))
    frequency = Column(String(20))  # e.g., "Monthly", "Weekly"
    description = Column(String(255))
    last_paid = Column(DateTime, nullable=True)