"""
Index Calculator Service

Service for calculating user wellbeing indexes based on financial,
health, and behavioral data.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
import uuid
from loguru import logger
from typing import Dict, Any, Optional

from models.models import User, VivIndex, FinancialAccount, FinancialTransaction, HealthDailySummary, VivLog

# ============================================================================
# Index Calculation Functions
# ============================================================================

def calculate_financial_wellbeing_index(user_id: str, db: Session) -> Dict[str, Any]:
    """
    Calculate financial wellbeing index (0-100).
    Returns dict with value and confidence.
    
    Formula:
    - Savings Rate (Savings Balance / Monthly Income): 40%
    - Discretionary Ratio (Incoming - Commitments): 40%
    - Debt Ratio (Outstanding / Income): 20%
    """
    try:
        # Get accounts
        accounts = db.query(FinancialAccount).filter(FinancialAccount.user_id == user_id).all()
        
        # Savings is STOCK (Accumulated capacity), Income is FLOW.
        savings_balance = sum(acc.current_balance for acc in accounts if str(acc.account_type).lower() == 'savings')
        debt_balance = sum(acc.current_balance for acc in accounts if str(acc.account_type).lower() == 'credit')
        
        # Get transactions for income/expenses (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        transactions = db.query(FinancialTransaction).filter(
            FinancialTransaction.user_id == user_id,
            FinancialTransaction.transaction_date >= thirty_days_ago
        ).all()
        
        income = sum(t.amount for t in transactions if t.amount > 0)
        expenses = sum(abs(t.amount) for t in transactions if t.amount < 0)
        
        if income <= 0:
            return {"value": 50.0, "confidence": 0.2} # Low confidence fallback
        
        # 1. Savings Buffer Ratio (Months of income saved)
        # Target: 3 months saved = 100 score. 0 saved = 0 score.
        months_saved = savings_balance / income
        savings_score = min(months_saved / 3.0, 1.0) * 100
        
        # 2. Free Cashflow Ratio
        free_cashflow = (income - expenses) / income
        # Target: 0.2 (20% savings rate) = 100 score. 0 = 50 score. < 0 = 0 score
        if free_cashflow < 0:
            cashflow_score = 0
        else:
            cashflow_score = 50 + min(free_cashflow / 0.2, 1.0) * 50
        
        # 3. Debt-to-Income (Monthly capacity)
        # Using simplified total debt balance vs monthly income
        dti = debt_balance / income
        # Target: 0 debt = 100. > 10x income = 0.
        debt_score = max(0, (1 - (dti / 10.0)) * 100)
        
        total = (savings_score * 0.4) + (cashflow_score * 0.4) + (debt_score * 0.2)
        return {"value": round(total, 2), "confidence": 0.8}
        
    except Exception as e:
        logger.error(f"Financial index error: {e}")
        return {"value": 50.0, "confidence": 0.0}

def calculate_time_saved_index(user_id: str, db: Session) -> Dict[str, Any]:
    """
    Calculate time saved index (0-100).
    Based on automation/action logs.
    """
    try:
        # Get logs from last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        logs = db.query(VivLog).filter(
            VivLog.user_id == user_id,
            VivLog.timestamp >= thirty_days_ago
        ).all()
        
        if not logs:
             return {"value": 0.0, "confidence": 0.5}

        # Weighted Activity
        automated_tasks = len([l for l in logs if "automated" in (str(l.decision_logic) or "").lower()])
        recommendations = len([l for l in logs if "recommendation" in (str(l.decision_logic) or "").lower()])
        actions = len([l for l in logs if "quick_action" in (str(l.user_intent) or "").lower()])
        
        # Score Logic: 10 actions/month = 100? No, let's scale.
        # Target: 20 meaningful interactions = 100 score.
        score_raw = (automated_tasks * 2) + (recommendations * 1.5) + (actions * 1)
        
        final_score = min((score_raw / 20.0) * 100, 100)
        return {"value": round(final_score, 2), "confidence": 0.8}
    except Exception as e:
        logger.error(f"Time index error: {e}")
        return {"value": 0.0, "confidence": 0.0}

def calculate_balance_index(user_id: str, financial_index: float, db: Session) -> Dict[str, Any]:
    """
    Calculate balance index (0-100) - health-enhanced.
    """
    try:
        # Get latest health summary
        latest_health = db.query(HealthDailySummary).filter(
            HealthDailySummary.user_id == user_id
        ).order_by(HealthDailySummary.date.desc()).first()
        
        if not latest_health:
            return {"value": 50.0, "confidence": 0.1}
        
        # Sleep (Target 7-9h)
        sleep_mins = latest_health.sleep_minutes or 360
        if 420 <= sleep_mins <= 540:
            sleep_score = 100
        else:
            diff = min(abs(sleep_mins - 420), abs(540 - sleep_mins))
            sleep_score = max(0, 100 - (diff / 2.0)) # Drop 1 pt per 2 mins off target
        
        # Active Mins (Target 30)
        active = latest_health.active_minutes or 0
        active_score = min(active / 30.0, 1.0) * 100
        
        # Financial Component (20% weight)
        
        total = (sleep_score * 0.4) + (active_score * 0.4) + (financial_index * 0.2)
        return {"value": round(total, 2), "confidence": 0.8}
        
    except Exception as e:
        logger.error(f"Balance index error: {e}")
        return {"value": 50.0, "confidence": 0.0}

def calculate_index_trend(user_id: str, current_val: float, index_type: str, db: Session) -> float:
    """
    Calculate trend vs previous snapshot (approx 7 days ago).
    """
    try:
        # Find closest snapshot to 7 days ago
        target_date = datetime.utcnow() - timedelta(days=7)
        # Look for range [8 days ago, 6 days ago] to find best match
        start_win = target_date - timedelta(days=1)
        end_win = target_date + timedelta(days=1)
        
        previous = db.query(VivIndex).filter(
            VivIndex.user_id == user_id,
            VivIndex.timestamp >= start_win,
            VivIndex.timestamp <= end_win
        ).order_by(VivIndex.timestamp.desc()).first()
        
        if not previous or not current_val:
            return 0.0
        
        prev_val = 0.0
        if index_type == "financial": prev_val = previous.financial_score
        elif index_type == "time_saved": prev_val = previous.time_score
        elif index_type == "balance": prev_val = previous.health_score 
        
        if prev_val == 0: return 0.0
        
        change = ((current_val - prev_val) / prev_val) * 100
        return round(change, 1)
        
    except Exception as e:
        logger.error(f"Trend calc error: {e}")
        return 0.0

# ============================================================================
# Main Calculator Function
# ============================================================================

def calculate_user_indexes(user_id: str, db: Session) -> dict:
    """
    Calculate all user indexes, persist snapshot (idempotent-ish), return results.
    """
    # 1. Check for existing snapshot today to avoid spam
    today = datetime.utcnow().date()
    existing = db.query(VivIndex).filter(
        VivIndex.user_id == user_id,
        func.date(VivIndex.timestamp) == today
    ).first()
    
    # Calculate
    fin_res = calculate_financial_wellbeing_index(user_id, db)
    time_res = calculate_time_saved_index(user_id, db)
    bal_res = calculate_balance_index(user_id, fin_res["value"], db)
    
    # Trends
    trends = {
        "financial": calculate_index_trend(user_id, fin_res["value"], "financial", db),
        "time_saved": calculate_index_trend(user_id, time_res["value"], "time_saved", db),
        "balance": calculate_index_trend(user_id, bal_res["value"], "balance", db)
    }
    
    # Weighted confidence
    avg_conf = (fin_res["confidence"] + time_res["confidence"] + bal_res["confidence"]) / 3.0
    
    if existing:
        # Update existing
        existing.financial_score = fin_res["value"]
        existing.time_score = time_res["value"]
        existing.health_score = bal_res["value"]
        existing.confidence = avg_conf
        existing.timestamp = datetime.utcnow() 
    else:
        # Create new
        viv_index = VivIndex(
            id=str(uuid.uuid4()),
            user_id=user_id,
            financial_score=fin_res["value"],
            time_score=time_res["value"],
            health_score=bal_res["value"],
            confidence=avg_conf,
            timestamp=datetime.utcnow(),
            snapshot_reason="Daily Calculation"
        )
        db.add(viv_index)
    
    db.commit()
    
    return {
        "financial_index": fin_res["value"],
        "time_saved_index": time_res["value"],
        "balance_index": bal_res["value"],
        "trends": trends,
        "confidence": avg_conf,
        "last_calculated": datetime.utcnow().isoformat()
    }

