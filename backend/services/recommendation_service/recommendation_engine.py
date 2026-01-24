from datetime import datetime, timedelta, timezone
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
    Generator: Optimize monthly subscriptions.
    Suggests review if there are multiple active bills.
    """
    bills = db.query(RecurringBill).filter(
        RecurringBill.user_id == user_id,
        RecurringBill.status == "active"
    ).all()
    
    if len(bills) >= 3:
        sorted_bills = sorted(bills, key=lambda b: b.amount)
        candidates = sorted_bills[:2] 
        count = len(candidates)
        savings = sum(b.amount for b in candidates)
        
        return {
            "id": "rec_fin_subscriptions",
            "category": "FINANCIAL",
            "title": "Optimize your monthly subscriptions",
            "body": f"We found {count} active subscriptions. Reviewing your least-used services could save you up to ${int(savings)}/month.",
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "cta": { "label": "Review Now", "href": "/subscriptions/review" },
            "priority": PRIORITY_FINANCIAL,
            "meta": { "unusedCount": count, "savingsMonthly": savings }
        }
        
    return None

def _generate_time_recommendations(user_id: str, db: Session) -> Optional[Dict[str, Any]]:
    """
    Generator: Automate morning commute.
    Looks for frequent weekday morning trips in the last 30 days.
    """
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    
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
                
    if morning_commute_count >= 5: # Increased threshold for higher confidence
        return {
            "id": "rec_time_commute",
            "category": "TIME",
            "title": "Automate your morning commute",
            "body": "Your pattern suggests a consistent morning commute. Automating bookings could save you 15 minutes of frustration daily.",
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "cta": { "label": "Set Up Automation", "href": "/commute/automation" },
            "priority": PRIORITY_TIME,
            "meta": { "commuteCount": morning_commute_count }
        }
        
    return None

def _generate_health_recommendations(user_id: str, db: Session) -> Optional[Dict[str, Any]]:
    """
    Generator: Schedule recovery time.
    Uses the most recent health data instead of strictly "yesterday".
    """
    # 1. Check Sleep Quality
    latest_health = db.query(HealthDailySummary).filter(
        HealthDailySummary.user_id == user_id
    ).order_by(HealthDailySummary.date.desc()).first()
    
    low_sleep = latest_health and latest_health.sleep_duration_minutes and latest_health.sleep_duration_minutes < 390 # 6.5 hours
    
    # 2. High Workout Load?
    last_24h = datetime.now(timezone.utc) - timedelta(hours=24)
    workouts = db.query(Workout).filter(
        Workout.user_id == user_id,
        Workout.start_time >= last_24h
    ).all()
    
    high_load = any(w.perceived_exertion and w.perceived_exertion >= 8 for w in workouts)
    
    if low_sleep or high_load:
        reason = "high physical load" if high_load else "low sleep efficiency"
        return {
            "id": "rec_health_recovery",
            "category": "HEALTH",
            "title": "Schedule recovery time",
            "body": f"Based on your recent {reason}, prioritize 20 minutes of mindfulness or a cool-down session today.",
            "createdAt": datetime.now(timezone.utc).isoformat(),
            "cta": { "label": "View Recovery Plan", "href": "/schedule" },
            "priority": PRIORITY_HEALTH,
            "meta": { "reason": reason }
        }
        
    return None
