from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import logging

from models.models import (
    VivIndex,
    User
)

logger = logging.getLogger(__name__)

def compute_treats(user_id: str, db: Session) -> List[Dict[str, Any]]:
    """
    Compute a list of 'Treat Yourself' rewards based on high performance.
    """
    completed_treats = []
    
    # Get latest scores
    latest_index = db.query(VivIndex).filter(VivIndex.user_id == user_id).order_by(VivIndex.timestamp.desc()).first()
    
    if not latest_index:
        return []
    
    # Thresholds for "overperforming"
    HIGH_SCORE_THRESHOLD = 80
    
    # 1. Financial Reward
    if latest_index.financial_score and latest_index.financial_score >= HIGH_SCORE_THRESHOLD:
        completed_treats.append({
            "id": "treat_fin_1",
            "category": "FINANCIAL",
            "title": "Splurge a little!",
            "body": "Your finances differ stability is excellent. Use 5% of your savings for that item on your wishlist.",
            "cta": {"label": "View Wishlist", "href": "/finance/wishlist"},
            "icon": "gift"
        })

    # 2. Health Reward
    if latest_index.health_score and latest_index.health_score >= HIGH_SCORE_THRESHOLD:
        completed_treats.append({
            "id": "treat_health_1",
            "category": "HEALTH",
            "title": "Spa Day",
            "body": "You've crushed your recovery goals. A massage would be well-earned.",
            "cta": {"label": "Book Spa", "href": "/concierge/book?q=spa"},
            "icon": "sparkles"
        })
        
    # 3. Time Reward
    if latest_index.time_score and latest_index.time_score >= HIGH_SCORE_THRESHOLD:
        completed_treats.append({
            "id": "treat_time_1",
            "category": "TIME",
            "title": "Weekend Getaway",
            "body": "Your productivity is through the roof. Plan a weekend off.",
            "cta": {"label": "Plan Trip", "href": "/travel"},
            "icon": "map"
        })
        
    return completed_treats
