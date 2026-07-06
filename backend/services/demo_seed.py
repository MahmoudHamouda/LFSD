"""
Keep the persona/demo accounts populated with *current* synthetic data.

The demo accounts (super@/finance@/health@/time@) exist to showcase a fully
populated product. Their data must always run up to *today*, or streaks break
and dashboards look stale. So this module does not seed once — it **refreshes**:
on every boot and on a recurring schedule it regenerates each demo account's
synthetic slice with rolling windows that end today (90 days of transactions,
30 days of health check-ins, historical VivIndex snapshots for trends, goals,
a statement and a financial score).

It is a no-op for every real user (only the fixed DEMO_ACCOUNTS are touched) and
deterministic (no randomness), so repeated runs converge to the same shape.
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

TXN_WINDOW_DAYS = 90
HEALTH_WINDOW_DAYS = 30  # => a 30-day check-in streak ending today


def _clear_synthetic(db: Session, uid: str) -> None:
    from models.models import (
        FinancialAccount,
        FinancialScore,
        FinancialTransaction,
        HealthDailySummary,
        LifeGoal,
        Statement,
        VivIndex,
    )

    # FK-safe order: transactions before accounts.
    for model in (
        FinancialTransaction,
        FinancialAccount,
        Statement,
        HealthDailySummary,
        LifeGoal,
        FinancialScore,
        VivIndex,
    ):
        db.query(model).filter(model.user_id == uid).delete(synchronize_session=False)


def _regenerate(db: Session, user) -> None:
    from models.models import (
        FinancialAccount,
        FinancialScore,
        FinancialTransaction,
        HealthDailySummary,
        LifeGoal,
        Statement,
        VivIndex,
    )

    uid = user.id
    now = datetime.now(timezone.utc)
    today = now.date()

    _clear_synthetic(db, uid)

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
    db.flush()

    db.add(
        Statement(
            user_id=uid,
            bank_name="Chase",
            period_start=now - timedelta(days=30),
            period_end=now,
            total_credits=10000.0,
            total_debits=6200.0,
            uploaded_at=now,
        )
    )

    # --- Transactions: rolling 90 days ending today --------------------
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

    for day in range(TXN_WINDOW_DAYS, -1, -1):
        d = now - timedelta(days=day)
        if d.day in (15, 30):
            _txn(checking.id, 5000.0, "Acme Corp Salary", "Income", d)
        if d.day == 1:
            _txn(checking.id, -2200.0, "Apartment Rent", "Rent", d)
        if day % 3 == 0:
            _txn(checking.id, -85.50, "Grocery Market", "Groceries", d)
        if day % 7 == 0:
            _txn(credit.id, -60.0, "Dining Out", "Dining", d)

    # --- Health check-ins: last 30 days ending today (streak = 30) -----
    for day in range(HEALTH_WINDOW_DAYS):
        # Small deterministic variation so it isn't perfectly flat.
        db.add(
            HealthDailySummary(
                user_id=uid,
                date=today - timedelta(days=day),
                sleep_duration_minutes=410 + (day % 5) * 10,
                sleep_quality_score=0.78 + (day % 4) * 0.03,
                hrv_average=45.0 + (day % 6),
                resting_heart_rate=56 + (day % 4),
                steps_count=7500 + (day % 7) * 300,
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

    # --- Financial score (current) ------------------------------------
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

    # --- VivIndex snapshots for trends (ending now) --------------------
    for days_ago, fin, hlth, tim in [
        (60, 70.0, 68.0, 63.0),
        (30, 74.0, 71.0, 66.0),
        (0, 78.0, 74.0, 69.0),
    ]:
        db.add(
            VivIndex(
                user_id=uid,
                financial_score=fin,
                health_score=hlth,
                time_score=tim,
                confidence=1.0,
                snapshot_reason="demo seed",
                timestamp=now - timedelta(days=days_ago),
            )
        )

    db.commit()


def refresh_demo_accounts(db: Session) -> int:
    """Regenerate current synthetic data for the demo accounts. Returns count."""
    from models.models import User

    refreshed = 0
    for email in DEMO_ACCOUNTS:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            continue
        try:
            _regenerate(db, user)
            refreshed += 1
        except Exception as e:
            db.rollback()
            logger.error("Demo refresh failed for %s: %s", email, e)
    if refreshed:
        logger.info("Refreshed demo data for %d account(s).", refreshed)
    return refreshed


# Backwards-compatible alias (previously named seed_demo_accounts).
seed_demo_accounts = refresh_demo_accounts
