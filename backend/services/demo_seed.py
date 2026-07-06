"""
Idempotent demo-data seeding for the persona accounts (super@/finance@/…).

Those accounts are meant to showcase a populated dashboard, but the persona seed
was never run against production, so they land on an empty landing page. This
module fills that gap: on startup, for each demo account that has *no* data yet,
it seeds a realistic slice (accounts, ~30 days of transactions, recent health
check-ins, goals, a financial score, and a VivIndex) so scores, streaks, and
goals render. It is a no-op for every real user and idempotent (keyed on the
presence of a VivIndex), so it is safe to run on every boot.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

logger = logging.getLogger("demo_seed")

DEMO_ACCOUNTS = [
    "super@helm.com",
    "finance@helm.com",
    "health@helm.com",
    "time@helm.com",
]


def _seed_one(db: Session, user) -> bool:
    from models.models import (
        FinancialAccount,
        FinancialScore,
        FinancialTransaction,
        HealthDailySummary,
        LifeGoal,
        VivIndex,
    )

    uid = user.id
    # Idempotency: if a VivIndex already exists, this account is populated.
    if db.query(VivIndex).filter(VivIndex.user_id == uid).first():
        return False

    now = datetime.now(timezone.utc)
    today = now.date()

    # --- Accounts ------------------------------------------------------
    checking = FinancialAccount(
        user_id=uid,
        institution_name="Chase",
        account_type="checking",
        current_balance=12500.00,
    )
    savings = FinancialAccount(
        user_id=uid,
        institution_name="Ally",
        account_type="savings",
        current_balance=45000.00,
    )
    credit = FinancialAccount(
        user_id=uid,
        institution_name="Amex",
        account_type="credit",
        current_balance=-1200.00,
        limit=15000.0,
    )
    db.add_all([checking, savings, credit])
    db.flush()  # assign ids

    # --- Transactions (last ~30 days) ---------------------------------
    def _txn(acct, amt, desc, cat, when):
        db.add(
            FinancialTransaction(
                user_id=uid,
                account_id=acct,
                amount=amt,
                description=desc,
                merchant_name=desc,
                category_primary=cat,
                currency_code="USD",
                transaction_date=when,
            )
        )

    for day in range(30, -1, -1):
        d = now - timedelta(days=day)
        if d.day in (15, 30):
            _txn(checking.id, 5000.0, "Acme Corp Salary", "Income", d)
        if d.day == 1:
            _txn(checking.id, -2200.0, "Apartment Rent", "Rent", d)
        if day % 3 == 0:
            _txn(checking.id, -85.50, "Grocery Market", "Groceries", d)
        if day % 7 == 0:
            _txn(credit.id, -60.0, "Dining Out", "Dining", d)

    # --- Health check-ins (last 14 days, incl. today → 14-day streak) --
    for day in range(14):
        db.add(
            HealthDailySummary(
                user_id=uid,
                date=today - timedelta(days=day),
                sleep_duration_minutes=430,
                sleep_quality_score=0.82,
                hrv_average=48.0,
                resting_heart_rate=58,
                steps_count=8200,
            )
        )

    # --- Goals ---------------------------------------------------------
    db.add(
        LifeGoal(
            user_id=uid,
            title="Emergency Fund",
            target_amount=15000.0,
            saved_amount=9000.0,
            type="emergency_fund",
            pillar="wealth",
            monthly_contribution_target=500.0,
            priority="high",
            target_date=now + timedelta(days=365),
        )
    )
    db.add(
        LifeGoal(
            user_id=uid,
            title="Dream Vacation",
            target_amount=5000.0,
            saved_amount=1800.0,
            type="savings",
            pillar="lifestyle",
            monthly_contribution_target=300.0,
            priority="medium",
            target_date=now + timedelta(days=240),
        )
    )

    # --- Scores --------------------------------------------------------
    db.add(
        FinancialScore(
            user_id=uid,
            overall_score=78.0,
            cashflow_stability_score=82.0,
            bills_coverage_score=88.0,
            discretionary_control_score=70.0,
            savings_rate_score=75.0,
            emergency_buffer_score=72.0,
            debt_load_score=85.0,
            networth_momentum_score=68.0,
            investment_health_score=74.0,
            time_window="month",
            total_monthly_income=10000.0,
            total_monthly_expenses=6200.0,
            total_monthly_bills=2200.0,
            total_monthly_savings=3800.0,
            total_assets_value=57500.0,
        )
    )
    db.add(
        VivIndex(
            user_id=uid,
            financial_score=78.0,
            health_score=74.0,
            time_score=69.0,
            confidence=1.0,
            snapshot_reason="demo seed",
        )
    )

    db.commit()
    logger.info("Seeded demo data for %s", user.email)
    return True


def seed_demo_accounts(db: Session) -> int:
    """Seed any un-populated demo accounts. Returns how many were seeded."""
    from models.models import User

    seeded = 0
    for email in DEMO_ACCOUNTS:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            continue
        try:
            if _seed_one(db, user):
                seeded += 1
        except Exception as e:
            db.rollback()
            logger.error("Demo seed failed for %s: %s", email, e)
    return seeded
