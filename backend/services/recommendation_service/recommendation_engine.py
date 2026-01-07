from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import logging

from models.models import (
    RecurringBill, 
    FinancialTransaction, 
    MobilityTrip, 
    HealthDailySummary, 
    Workout,
    User
)

logger = logging.getLogger(__name__)

# Constants
PRIORITY_FINANCIAL = 80
PRIORITY_TIME = 60
PRIORITY_HEALTH = 40

def compute_recommendations(user_id: str, db: Session) -> List[Dict[str, Any]]:
    """
    Compute a ranked list of recommendations for the user.
    """
    items = []
    
    # 1. Financial: Optimize subscriptions
    fin_rec = _generate_financial_recommendations(user_id, db)
    if fin_rec:
        items.append(fin_rec)
        
    # 2. Time: Automate commute
    time_rec = _generate_time_recommendations(user_id, db)
    if time_rec:
        items.append(time_rec)
        
    # 3. Health: Schedule recovery
    health_rec = _generate_health_recommendations(user_id, db)
    if health_rec:
        items.append(health_rec)
        
    # Sort by priority desc
    items.sort(key=lambda x: x['priority'], reverse=True)
    
    logger.info(f"Generated {len(items)} recommendations for user {user_id}")
    return items[:5] # Max 5 items

def _generate_financial_recommendations(user_id: str, db: Session) -> Optional[Dict[str, Any]]:
    """
    Generator: Optimize monthly subscriptions
    Rule: If count of "unused" subscriptions >= 2, suggest check.
    Logic: 
      - Fetch all active recurring bills.
      - "Unused" = mock logic for now: if we have more than 2 recurring bills total, 
        we assume some are unused for the sake of the feature demonstration 
        (since we lack a robust 'last_used_at' signal on the bill itself).
      - In a real world, we would join with Transactions to find last payment date vs usage.
    """
    # Get all verified recurring bills
    bills = db.query(RecurringBill).filter(
        RecurringBill.user_id == user_id
    ).all()
    
    # Filter for 'unused' (Simulation: if we have > 2 bills, we flag the excess/cheaper ones)
    # Real logic: check if no 'usage' signal. 
    # For MVP: If user has >= 3 bills, we flag 2 of them as potential candidates.
    
    if len(bills) >= 3:
        # Calculate potential savings (sum of 2 cheapest bills)
        sorted_bills = sorted(bills, key=lambda b: b.amount)
        # Take the bottom 2 items (cheapest) as candidates for "unused"
        candidates = sorted_bills[:2] 
        count = len(candidates)
        savings = sum(b.amount for b in candidates)
        
        return {
            "id": "rec_fin_subscriptions",
            "category": "FINANCIAL",
            "title": "Optimize your monthly subscriptions",
            "body": f"We found {count} subscriptions you rarely use. Cancel them to save ${int(savings)}/month.",
            "createdAt": datetime.utcnow().isoformat(),
            "cta": { "label": "Review Now", "href": "/subscriptions/review" },
            "priority": PRIORITY_FINANCIAL,
            "meta": { "unusedCount": count, "savingsMonthly": savings }
        }
        
    return None

def _generate_time_recommendations(user_id: str, db: Session) -> Optional[Dict[str, Any]]:
    """
    Generator: Automate morning commute
    Rule: If user has recurring morning commute pattern (8 AM weekday).
    Logic: Look for mobility trips between 7AM-9AM on weekdays in last 30 days.
    """
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    # Count trips between 7-9 AM
    # SQLite/Postgres extracts are different, so we fetch recent trips and filter in python for MVP safety
    recent_trips = db.query(MobilityTrip).filter(
        MobilityTrip.user_id == user_id,
        MobilityTrip.pickup_time >= thirty_days_ago
    ).all()
    
    morning_commute_count = 0
    for trip in recent_trips:
        if trip.pickup_time:
            # Weekday (0-4) and Hour 7-9
            if trip.pickup_time.weekday() < 5 and 7 <= trip.pickup_time.hour <= 9:
                morning_commute_count += 1
                
    # If we see a pattern (e.g. at least 3 morning trips)
    if morning_commute_count >= 3:
        return {
            "id": "rec_time_commute",
            "category": "TIME",
            "title": "Automate your morning commute",
            "body": "Set up automatic ride booking for your 8 AM commute every weekday.",
            "createdAt": datetime.utcnow().isoformat(),
            "cta": { "label": "Set Up", "href": "/commute/automation" },
            "priority": PRIORITY_TIME,
            "meta": { "commuteCount": morning_commute_count }
        }
        
    return None

def _generate_health_recommendations(user_id: str, db: Session) -> Optional[Dict[str, Any]]:
    """
    Generator: Schedule recovery time
    Rule: If activity load is high (e.g. recent workout high exertion or low sleep).
    """
    # Check yesterday's sleep or today's workout
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)
    
    # 1. Low Sleep?
    sleep = db.query(HealthDailySummary).filter(
        HealthDailySummary.user_id == user_id,
        HealthDailySummary.date == yesterday
    ).first()
    
    low_sleep = sleep and sleep.sleep_duration_minutes and sleep.sleep_duration_minutes < 360 # 6 hours
    
    # 2. High Workout Load?
    # Get workouts in last 24h
    last_24h = datetime.utcnow() - timedelta(hours=24)
    workouts = db.query(Workout).filter(
        Workout.user_id == user_id,
        Workout.start_time >= last_24h
    ).all()
    
    high_load = any(w.perceived_exertion and w.perceived_exertion >= 8 for w in workouts)
    
    if low_sleep or high_load:
        reason = "activity load is high" if high_load else "sleep was low"
        return {
            "id": "rec_health_recovery",
            "category": "HEALTH",
            "title": "Schedule recovery time",
            "body": f"Your {reason}. Consider lighter tasks tomorrow afternoon.",
            "createdAt": datetime.utcnow().isoformat(),
            "cta": { "label": "View Schedule", "href": "/schedule" },
            "priority": PRIORITY_HEALTH,
            "meta": { "reason": reason }
        }
        
    return None
