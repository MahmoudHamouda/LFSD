from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any, Set
from sqlalchemy.orm import Session
import logging
import uuid

from models.models import (
    VivIndex,
    HealthDailySummary,
    FinancialAccount
)

logger = logging.getLogger(__name__)

# Configuration
PILLAR_THRESHOLDS = {
    "FINANCIAL": 85,
    "HEALTH": 80,
    "TIME": 80
}
CRISIS_THRESHOLD = 45  # Suppression threshold for treats if any index is collapsing

def compute_treats(user_id: str, db: Session, user_tz: timezone = timezone.utc) -> List[Dict[str, Any]]:
    """
    Compute a list of 'Treat Yourself' suggestions based on high performance.
    Ensures deduplication, normalization, and safety (crisis detection).
    """
    suggested_treats = []
    categories_covered: Set[str] = set()
    
    # 1. Get Latest Scores
    latest_index = db.query(VivIndex).filter(VivIndex.user_id == user_id).order_by(VivIndex.timestamp.desc()).first()
    
    if not latest_index:
        logger.info(f"No VivIndex found for user {user_id}, skipping treats.")
        return []

    # 2. Crisis Detection
    # If any score is critically low, suppress treats that involve spending or time displacement.
    scores = [
        latest_index.financial_score or 50,
        latest_index.health_score or 50,
        latest_index.time_score or 50
    ]
    is_in_crisis = any(s < CRISIS_THRESHOLD for s in scores)
    
    # 3. Financial Context (for verification)
    savings_accounts = db.query(FinancialAccount).filter(
        FinancialAccount.user_id == user_id,
        FinancialAccount.account_type == "savings"
    ).all()
    total_savings = sum(acc.current_balance for acc in savings_accounts)

    date_str = datetime.now(user_tz).strftime("%Y%m%d")

    # --- Score-Based Logic ---

    # 1. Financial Reward
    if (latest_index.financial_score and 
        latest_index.financial_score >= PILLAR_THRESHOLDS["FINANCIAL"] and 
        not is_in_crisis):
        
        # Only suggest if they have at least 1000 in savings to make "5% splurge" meaningful/safe
        if total_savings >= 1000:
            splurge_val = round(total_savings * 0.05, 2)
            suggested_treats.append({
                "id": f"treat_fin_{date_str}_{uuid.uuid4().hex[:6]}",
                "category": "FINANCIAL",
                "title": "Smart Splurge!",
                "body": f"Your financial stability is excellent. You've earned a small reward—consider allocating up to ${splurge_val} (5% of savings) for something special.",
                "cta": {"label": "View Finance", "href": "/finance"},
                "icon": "gift"
            })
            categories_covered.add("FINANCIAL")

    # 2. Health Reward
    if (latest_index.health_score and 
        latest_index.health_score >= PILLAR_THRESHOLDS["HEALTH"] and 
        not is_in_crisis):
        
        suggested_treats.append({
            "id": f"treat_health_{date_str}_{uuid.uuid4().hex[:6]}",
            "category": "HEALTH",
            "title": "Recovery Focus",
            "body": "Your health metrics are peak. A professional massage or spa session would optimize your recovery further.",
            "cta": {"label": "Health Dashboard", "href": "/health"},
            "icon": "sparkles"
        })
        categories_covered.add("HEALTH")
        
    # 3. Time Reward
    if (latest_index.time_score and 
        latest_index.time_score >= PILLAR_THRESHOLDS["TIME"] and 
        not is_in_crisis):
        
        suggested_treats.append({
            "id": f"treat_time_{date_str}_{uuid.uuid4().hex[:6]}",
            "category": "TIME",
            "title": "Time Surplus",
            "body": "Your productivity is exceptionally high. You've created enough margin for a restful weekend getaway.",
            "cta": {"label": "Explore Time", "href": "/time"},
            "icon": "map"
        })
        categories_covered.add("TIME")
        
    # --- Behavior-Based Fallbacks (Only if category not covered by scores) ---

    # Check most recent data (Health)
    recent_summary = db.query(HealthDailySummary).filter(
        HealthDailySummary.user_id == user_id
    ).order_by(HealthDailySummary.date.desc()).first()
    
    if recent_summary and not is_in_crisis:
        # High Steps
        if ("HEALTH" not in categories_covered and 
            (recent_summary.steps_count or 0) > 10000): # Normalized to 10k for high performance
            
            suggested_treats.append({
                "id": f"treat_health_steps_{date_str}",
                "category": "HEALTH",
                "title": "Peak Activity Bonus",
                "body": f"You smashed {recent_summary.steps_count} steps! Treat your feet to a professional reflexology session.",
                "cta": {"label": "Wellness Options", "href": "/health"},
                "icon": "activity"
            })
            categories_covered.add("HEALTH")

        # Good Sleep
        if ("HEALTH" not in categories_covered and 
            (recent_summary.sleep_duration_minutes or 0) > 480): # > 8 hours
            
            suggested_treats.append({
                "id": f"treat_health_sleep_{date_str}",
                "category": "HEALTH",
                "title": "Sleep Champion",
                "body": "Exceptional rest efficiency detected. Maintain this momentum with a premium silk sleep mask or aromatherapy set.",
                "cta": {"label": "Sleep Shop", "href": "/health/sleep"},
                "icon": "moon"
            })
            categories_covered.add("HEALTH")

    logger.info(f"Generated {len(suggested_treats)} suggested treats for user {user_id}")
    return suggested_treats
