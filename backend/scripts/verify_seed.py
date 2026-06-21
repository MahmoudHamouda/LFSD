import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database import SessionLocal
from models.models import (
    User,
    FinancialTransaction,
    HealthDailySummary,
    CalendarEvent,
    LifeGoal,
)
from sqlalchemy import func


def verify():
    db = SessionLocal()
    users = db.query(User).all()

    print(
        f"{'User Email':<20} | {'Txns':<5} | {'Health':<6} | {'Events':<6} | {'Goals':<5}"
    )
    print("-" * 60)

    for user in users:
        txns = (
            db.query(func.count(FinancialTransaction.id))
            .filter_by(user_id=user.id)
            .scalar()
        )
        health = (
            db.query(func.count(HealthDailySummary.id))
            .filter_by(user_id=user.id)
            .scalar()
        )
        events = (
            db.query(func.count(CalendarEvent.id)).filter_by(user_id=user.id).scalar()
        )
        goals = db.query(func.count(LifeGoal.id)).filter_by(user_id=user.id).scalar()

        print(f"{user.email:<20} | {txns:<5} | {health:<6} | {events:<6} | {goals:<5}")

    db.close()


if __name__ == "__main__":
    verify()
