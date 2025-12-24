"""
Analytics routes for viewing user interactions and usage patterns.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
from models.database import get_db
from models.models import DBInteraction, DBPriceHistory
from core.authentication import get_current_user
from core.rate_limiting import limiter
import json

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/interactions")
@limiter.limit("60/minute")
async def get_user_interactions(
    limit: int = 50,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get user's interaction history."""
    user_id = current_user.id
    
    interactions = db.query(DBInteraction).filter(
        DBInteraction.user_id == user_id
    ).order_by(DBInteraction.timestamp.desc()).limit(limit).all()
    
    return {
        "total": len(interactions),
        "interactions": [
            {
                "id": i.id,
                "type": i.interaction_type,
                "provider": i.provider,
                "details": json.loads(i.details) if i.details else {},
                "timestamp": i.timestamp.isoformat(),
                "conversation_id": i.conversation_id
            }
            for i in interactions
        ]
    }


@router.get("/price-history")
@limiter.limit("60/minute")
async def get_price_history(
    provider: str = None,
    limit: int = 50,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get user's price history."""
    user_id = current_user.id
    
    query = db.query(DBPriceHistory).filter(DBPriceHistory.user_id == user_id)
    
    if provider:
        query = query.filter(DBPriceHistory.provider == provider)
    
    prices = query.order_by(DBPriceHistory.timestamp.desc()).limit(limit).all()
    
    return {
        "total": len(prices),
        "prices": [
            {
                "id": p.id,
                "provider": p.provider,
                "ride_type": p.ride_type,
                "price": p.price_estimate,
                "currency": p.currency,
                "start": json.loads(p.start_location) if p.start_location else None,
                "end": json.loads(p.end_location) if p.end_location else None,
                "timestamp": p.timestamp.isoformat()
            }
            for p in prices
        ]
    }


@router.get("/popular-routes")
@limiter.limit("60/minute")
async def get_popular_routes(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get user's most requested routes."""
    user_id = current_user.id
    
    # Group by start/end location pairs
    routes = db.query(
        DBPriceHistory.start_location,
        DBPriceHistory.end_location,
        func.count(DBPriceHistory.id).label('count'),
        func.avg(DBPriceHistory.price_estimate).label('avg_price')
    ).filter(
        DBPriceHistory.user_id == user_id
    ).group_by(
        DBPriceHistory.start_location,
        DBPriceHistory.end_location
    ).order_by(func.count(DBPriceHistory.id).desc()).limit(10).all()
    
    return {
        "routes": [
            {
                "start": json.loads(r.start_location) if r.start_location else None,
                "end": json.loads(r.end_location) if r.end_location else None,
                "request_count": r.count,
                "average_price": round(r.avg_price, 2)
            }
            for r in routes
        ]
    }


@router.get("/provider-usage")
@limiter.limit("60/minute")
async def get_provider_usage(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get provider usage statistics."""
    user_id = current_user.id
    
    # Count interactions by provider
    provider_stats = db.query(
        DBInteraction.provider,
        func.count(DBInteraction.id).label('count')
    ).filter(
        DBInteraction.user_id == user_id
    ).group_by(DBInteraction.provider).all()
    
    return {
        "providers": [
            {
                "provider": p.provider,
                "interaction_count": p.count
            }
            for p in provider_stats
        ]
    }
