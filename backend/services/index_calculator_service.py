"""
Index Calculator Service

Service for calculating user wellbeing indexes based on financial,
health, and behavioral data.
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid

from models.models import User, VivIndex, FinancialAccount, Transaction, HealthDailySummary, VivLog

# ============================================================================
# Index Calculation Functions
# ============================================================================

def calculate_financial_wellbeing_index(user_id: str, db: Session) -> float:
    """
    Calculate financial wellbeing index (0-100).
    
    Formula:
    - Savings rate: 30%
    - Discretionary income: 40%
    - Debt ratio: 30%
    """
    # Get accounts
    accounts = db.query(FinancialAccount).filter(FinancialAccount.user_id == user_id).all()
    
    savings = sum(acc.current_balance for acc in accounts if acc.account_type.lower() == 'savings')
    debts = sum(acc.current_balance for acc in accounts if acc.account_type.lower() == 'credit')
    
    # Get transactions for income/expenses (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.transaction_date >= thirty_days_ago
    ).all()
    
    income = sum(t.amount for t in transactions if t.amount > 0)
    expenses = sum(abs(t.amount) for t in transactions if t.amount < 0)
    
    if income <= 0:
        return 50.0
    
    # Calculate components
    savings_rate = (savings / income) * 100 if income > 0 else 0
    discretionary_ratio = ((income - expenses) / income) * 100 if income > 0 else 0
    debt_ratio = (debts / income) * 100 if income > 0 else 0
    
    # Normalize to 0-100 scale
    savings_score = min(savings_rate / 50 * 100, 100) * 0.3  # Target 50% savings rate
    discretionary_score = min(discretionary_ratio / 40 * 100, 100) * 0.4  # Target 40% discretionary
    debt_score = max(0, (1 - debt_ratio / 100) * 100) * 0.3  # Lower debt is better
    
    total = savings_score + discretionary_score + debt_score
    return round(min(max(total, 0), 100), 2)

def calculate_time_saved_index(user_id: str, db: Session) -> float:
    """
    Calculate time saved index (0-100).
    
    Based on VivLogs (automation, recommendations).
    """
    # Get logs from last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    logs = db.query(VivLog).filter(
        VivLog.user_id == user_id,
        VivLog.timestamp >= thirty_days_ago
    ).all()
    
    # Count different activity types based on intent/logic
    automated_tasks = len([l for l in logs if "automated" in (l.decision_logic or "").lower()])
    recommendations_used = len([l for l in logs if "recommendation" in (l.decision_logic or "").lower()])
    quick_actions = len([l for l in logs if "quick_action" in (l.user_intent or "").lower()])
    
    # Calculate score
    score = (automated_tasks * 10) + (recommendations_used * 5) + (quick_actions * 2)
    
    # Normalize to 0-100
    normalized = min(score, 100)
    return round(normalized, 2)

def calculate_balance_index(user_id: str, financial_index: float, db: Session) -> float:
    """
    Calculate balance index (0-100) - health-enhanced.
    
    Formula:
    - Sleep score: 30%
    - Recovery: 30% (derived from HRV/Sleep)
    - Activity load: 20%
    - Financial wellbeing: 20%
    """
    # Get latest health summary
    latest_health = db.query(HealthDailySummary).filter(
        HealthDailySummary.user_id == user_id
    ).order_by(HealthDailySummary.date.desc()).first()
    
    if not latest_health:
        return None
    
    # Calculate components
    sleep_score = (latest_health.sleep_quality_score or 50) * 0.3
    
    # Derive recovery from HRV (simple normalization)
    hrv = latest_health.hrv_average or 50
    recovery_score = min(hrv / 100 * 100, 100) * 0.3
    
    # Derive activity from steps
    steps = latest_health.steps_count or 0
    activity_score = min(steps / 10000 * 100, 100) * 0.2
    
    financial_score_component = financial_index * 0.2
    
    total = sleep_score + recovery_score + activity_score + financial_score_component
    return round(min(max(total, 0), 100), 2)

def calculate_index_trend(user_id: str, current_index: float, index_type: str, db: Session) -> float:
    """
    Calculate trend for an index by comparing to previous period.
    
    Returns percentage change.
    """
    # Get index from 7 days ago
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    previous = db.query(VivIndex).filter(
        VivIndex.user_id == user_id,
        VivIndex.timestamp <= seven_days_ago
    ).order_by(VivIndex.timestamp.desc()).first()
    
    if not previous:
        return 0.0
    
    # Get previous value based on index type
    previous_value = 0
    if index_type == "financial":
        previous_value = previous.financial_score
    elif index_type == "time_saved":
        previous_value = previous.time_score
    elif index_type == "balance":
        # Balance score wasn't explicitly stored in VivIndex in the new schema, 
        # but let's assume it's roughly the average or we can add it.
        # Wait, VivIndex has financial, health, time. 
        # 'Balance' seems to be a composite or synonymous with Health in some contexts, 
        # but here it's calculated separately.
        # Let's map 'balance' to 'health_score' for trend tracking if it fits, 
        # or just return 0 if not tracked.
        # Actually, let's use health_score as the proxy for balance/wellbeing.
        previous_value = previous.health_score
    
    if previous_value == 0:
        return 0.0
    
    # Calculate percentage change
    change = ((current_index - previous_value) / previous_value) * 100
    return round(change, 2)

# ============================================================================
# Main Calculator Function
# ============================================================================

def calculate_user_indexes(user_id: str, db: Session) -> dict:
    """
    Calculate all user indexes and store in database.
    
    Returns calculated indexes with trends.
    """
    
    # Calculate indexes
    financial_index = calculate_financial_wellbeing_index(user_id, db)
    time_saved_index = calculate_time_saved_index(user_id, db)
    balance_index = calculate_balance_index(user_id, financial_index, db) or 50.0
    
    # Calculate trends
    financial_trend = calculate_index_trend(user_id, financial_index, "financial", db)
    time_saved_trend = calculate_index_trend(user_id, time_saved_index, "time_saved", db)
    balance_trend = calculate_index_trend(user_id, balance_index, "balance", db)
    
    # Store in database
    viv_index = VivIndex(
        id=str(uuid.uuid4()),
        user_id=user_id,
        financial_score=financial_index,
        time_score=time_saved_index,
        health_score=balance_index, # Mapping balance to health_score for storage
        timestamp=datetime.utcnow(),
        snapshot_reason="Daily Calculation"
    )
    
    db.add(viv_index)
    db.commit()
    
    return {
        "financialWellbeingIndex": financial_index,
        "timeSavedIndex": time_saved_index,
        "balanceIndex": balance_index,
        "trend": {
            "financialWellbeing": financial_trend,
            "timeSaved": time_saved_trend,
            "balance": balance_trend
        },
        "lastCalculatedAt": viv_index.timestamp.isoformat()
    }
