"""
Index Calculator Service

Service for calculating user wellbeing indexes based on financial,
health, and behavioral data.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone
import uuid
import logging
from typing import Dict, Any, Optional

from models.models import (
    User,
    VivIndex,
    FinancialAccount,
    FinancialTransaction,
    HealthDailySummary,
    VivLog,
)

logger = logging.getLogger(__name__)

# ============================================================================
# Index Calculation Functions
# ============================================================================


def calculate_financial_wellbeing_index(user_id: str, db: Session) -> Dict[str, Any]:
    """
    Calculate financial wellbeing index (0-100).

    Formula:
    - Savings Buffer (Stock coverage): 40%
    - Free Cashflow Ratio (Savings Rate): 40%
    - Debt-to-Income Ratio: 20%
    """
    try:
        # 1. Fetch Accounts
        accounts = (
            db.query(FinancialAccount).filter(FinancialAccount.user_id == user_id).all()
        )

        # Treatment of sign conventions:
        # Savings: positive current_balance
        # Credit/Loans: we assume positive balance means liability (or abs() to be safe)
        savings_balance = sum(
            acc.current_balance
            for acc in accounts
            if str(acc.account_type).lower() == "savings"
        )
        debt_balance = sum(
            abs(acc.current_balance)
            for acc in accounts
            if str(acc.account_type).lower() in ["credit", "loan", "liability"]
        )

        # 2. Fetch Transactions (Flow)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        transactions = (
            db.query(FinancialTransaction)
            .filter(
                FinancialTransaction.user_id == user_id,
                FinancialTransaction.transaction_date >= thirty_days_ago,
            )
            .all()
        )

        # Income vs Expenses
        income = sum(t.amount for t in transactions if t.amount > 0)
        expenses = sum(abs(t.amount) for t in transactions if t.amount < 0)

        if income <= 1.0:  # Prevent division by near-zero or zero
            return {"value": 50.0, "confidence": 0.1}

        # 3. Component Scores

        # A. Savings Buffer (Months of income covered by savings)
        # Target: 6 months saved = 100 score. (Standard conservative baseline)
        months_saved = savings_balance / income
        savings_score = min(months_saved / 6.0, 1.0) * 100

        # B. Free Cashflow (Surplus after expenses)
        # Target: 20% surplus = 100. 0% = 50. Negative = 0.
        surplus_ratio = (income - expenses) / income
        if surplus_ratio < 0:
            cashflow_score = max(
                0, 50 + (surplus_ratio * 100)
            )  # Rapid drop if negative
        else:
            cashflow_score = 50 + (min(surplus_ratio / 0.2, 1.0) * 50)

        # C. Debt Ratio (DTI Proxy)
        # Target: 0 debt = 100. Debt > 3x annual income (36x monthly) = 0.
        dti = debt_balance / income
        debt_score = max(0, (1 - (dti / 36.0)) * 100)

        weighted_total = (
            (savings_score * 0.4) + (cashflow_score * 0.4) + (debt_score * 0.2)
        )
        return {"value": round(weighted_total, 2), "confidence": 0.85}

    except Exception as e:
        logger.error(f"Financial index calculation failed for {user_id}: {e}")
        return {"value": 50.0, "confidence": 0.0}


def calculate_time_saved_index(user_id: str, db: Session) -> Dict[str, Any]:
    """
    Calculate time saved index (0-100).
    Based on automation/action logs with normalized weights.
    """
    try:
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        logs = (
            db.query(VivLog)
            .filter(VivLog.user_id == user_id, VivLog.timestamp >= thirty_days_ago)
            .all()
        )

        if not logs:
            return {"value": 20.0, "confidence": 0.3}  # Baseline for new users

        # Structured Intent/Logic matching
        # Better than free-text: check specific prefixes or metadata if available
        # Fallback to normalized substring checks

        count_automation = 0
        count_delegation = 0
        count_optimization = 0

        for log in logs:
            logic = (str(log.decision_logic) or "").lower()
            intent = (str(log.user_intent) or "").lower()

            if "automated" in logic or "booking" in intent:
                count_automation += 1
            if "recommendation" in logic or "advisory" in intent:
                count_optimization += 1
            if "quick_action" in intent or "shortcut" in intent:
                count_delegation += 1

        # Weighted scaling: Automation (5 mins saved), Optimization (2 mins), Delegation (1 min)
        # Target: 60 minutes saved per month = 100 score.
        total_mins_saved = (
            (count_automation * 5) + (count_optimization * 2) + (count_delegation * 1)
        )

        final_score = min((total_mins_saved / 60.0) * 100, 100)
        return {"value": round(final_score, 2), "confidence": 0.75}

    except Exception as e:
        logger.error(f"Time index calculation failed for {user_id}: {e}")
        return {"value": 50.0, "confidence": 0.0}


def calculate_health_index(user_id: str, db: Session) -> Dict[str, Any]:
    """
    Calculate health index (0-100).
    Focuses on sleep and activity consistency.
    """
    try:
        # Get most recent 7 summaries for consistency tracking
        summaries = (
            db.query(HealthDailySummary)
            .filter(HealthDailySummary.user_id == user_id)
            .order_by(HealthDailySummary.date.desc())
            .limit(7)
            .all()
        )

        if not summaries:
            return {"value": 50.0, "confidence": 0.1}

        latest = summaries[0]

        # 1. Sleep Score (Target 7.5 - 8.5 hours)
        # 450 - 510 minutes
        sleep_mins = latest.sleep_duration_minutes or 420
        if 450 <= sleep_mins <= 510:
            sleep_score = 100
        else:
            # Drop 1% for every 2 mins away from target range
            diff = min(abs(sleep_mins - 450), abs(510 - sleep_mins))
            sleep_score = max(0, 100 - (diff / 2.0))

        # 2. Activity Score (Target 10,000 steps)
        steps = latest.steps_count or 0
        steps_score = (
            min(steps / 10000.0, 1.2) * 80
        )  # Up to 120% target, but capped at logic stage

        # 3. Consistency (Bonus)
        # If mean volume of activity is stable
        consistency_bonus = 0
        if len(summaries) >= 3:
            avg_steps = sum(s.steps_count or 0 for s in summaries) / len(summaries)
            if avg_steps > 5000:
                consistency_bonus = 10

        final_health = (sleep_score * 0.5) + (steps_score * 0.4) + consistency_bonus
        return {"value": round(min(final_health, 100), 2), "confidence": 0.9}

    except Exception as e:
        logger.error(f"Health index calculation failed for {user_id}: {e}")
        return {"value": 50.0, "confidence": 0.0}


def calculate_index_trend(
    user_id: str, current_val: float, index_type: str, db: Session
) -> float:
    """
    Calculate trend vs previous snapshot (approx 7 days ago).
    """
    try:
        target_date = datetime.utcnow() - timedelta(days=7)
        start_win = target_date - timedelta(days=2)
        end_win = target_date + timedelta(days=2)

        previous = (
            db.query(VivIndex)
            .filter(
                VivIndex.user_id == user_id,
                VivIndex.timestamp >= start_win,
                VivIndex.timestamp <= end_win,
            )
            .order_by(VivIndex.timestamp.desc())
            .first()
        )

        if not previous or not current_val:
            return 0.0

        # Correctly map index_type to VivIndex columns
        mapping = {
            "financial": previous.financial_score,
            "time": previous.time_score,
            "health": previous.health_score,
        }
        prev_val = mapping.get(index_type, 0.0)

        if not prev_val or prev_val == 0:
            return 0.0

        change = ((current_val - prev_val) / prev_val) * 100
        return round(change, 1)

    except Exception as e:
        logger.error(f"Trend calculation failed: {e}")
        return 0.0


# ============================================================================
# Main Calculator Entry Point
# ============================================================================


def calculate_user_indexes(user_id: str, db: Session) -> dict:
    """
    Calculate all user indexes, persist snapshot, and return current stats.
    """
    # 1. Check for duplicate calc today
    today = datetime.utcnow().date()
    existing = (
        db.query(VivIndex)
        .filter(VivIndex.user_id == user_id, func.date(VivIndex.timestamp) == today)
        .order_by(VivIndex.timestamp.desc())
        .first()
    )

    # 2. Run Calculations
    fin_res = calculate_financial_wellbeing_index(user_id, db)
    time_res = calculate_time_saved_index(user_id, db)
    health_res = calculate_health_index(user_id, db)

    # 3. Trends
    trends = {
        "financial": calculate_index_trend(user_id, fin_res["value"], "financial", db),
        "time": calculate_index_trend(user_id, time_res["value"], "time", db),
        "health": calculate_index_trend(user_id, health_res["value"], "health", db),
    }

    # 4. Aggregated Metrics
    avg_conf = (
        fin_res["confidence"] + time_res["confidence"] + health_res["confidence"]
    ) / 3.0
    now = datetime.utcnow()

    if existing:
        # Update existing snapshot
        existing.financial_score = fin_res["value"]
        existing.time_score = time_res["value"]
        existing.health_score = health_res["value"]
        existing.confidence = avg_conf
        existing.timestamp = now
    else:
        # Create new snapshot
        viv_index = VivIndex(
            id=str(uuid.uuid4()),
            user_id=user_id,
            financial_score=fin_res["value"],
            time_score=time_res["value"],
            health_score=health_res["value"],
            confidence=avg_conf,
            timestamp=now,
            snapshot_reason="Daily Calculation",
        )
        db.add(viv_index)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to persist index snapshot for {user_id}: {e}")

    return {
        "financial_index": fin_res["value"],
        "time_saved_index": time_res["value"],
        "health_index": health_res["value"],
        "trends": trends,
        "confidence": avg_conf,
        "last_calculated": now.isoformat(),
    }
