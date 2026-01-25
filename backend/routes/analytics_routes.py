"""
Analytics routes for viewing user interactions and usage patterns.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any
from models.database import get_db
from models.models import ActivityFeed, MobilityTrip, Order
import json

@router.get("/interactions")
@limiter.limit("60/minute")
async def get_user_interactions(
    request: Request,
    limit: int = 50,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get user's activity/interaction history."""
    user_id = current_user.id
    
    # Use ActivityFeed as primary source of "interactions"
    query = db.query(ActivityFeed).filter(ActivityFeed.user_id == user_id)
    interactions = query.order_by(ActivityFeed.created_at.desc()).limit(limit).all()
    
    return {
        "total": len(interactions),
        "interactions": [
            {
                "id": i.id,
                "type": i.action_type,
                "description": i.description,
                "details": i.metadata_json,
                "timestamp": i.created_at.isoformat()
            }
            for i in interactions
        ]
    }


@router.get("/price-history")
@limiter.limit("60/minute")
async def get_price_history(
    request: Request,
    provider: str = None,
    limit: int = 50,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get user's mobility price history (trips)."""
    user_id = current_user.id
    
    query = db.query(MobilityTrip).filter(MobilityTrip.user_id == user_id)
    
    if provider:
        query = query.filter(MobilityTrip.provider == provider)
    
    # Exclude trips without cost
    query = query.filter(MobilityTrip.cost_amount.isnot(None))
    
    trips = query.order_by(MobilityTrip.id.desc()).limit(limit).all() # No timestamp directly on Trip? 
    # MoblityTrip has pickup_time
    
    results = []
    for t in trips:
        ts = t.pickup_time or datetime.utcnow()
        results.append({
            "id": t.id,
            "provider": t.provider,
            "ride_type": t.trip_type,
            "price": t.cost_amount,
            "currency": t.currency,
            "start": {"lat": t.origin_lat, "lon": t.origin_lon},
            "end": {"lat": t.destination_lat, "lon": t.destination_lon},
            "timestamp": ts.isoformat()
        })
        
    return {
        "total": len(results),
        "prices": results
    }


@router.get("/popular-routes")
@limiter.limit("60/minute")
async def get_popular_routes(
    request: Request,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get user's most requested routes."""
    user_id = current_user.id
    
    # Group by lat/lon roughly? 
    # For now, simplistic exact match on coords (unlikely to hit often without snapping)
    # or just return raw list
    
    routes = db.query(
        MobilityTrip.origin_lat,
        MobilityTrip.origin_lon,
        MobilityTrip.destination_lat,
        MobilityTrip.destination_lon,
        func.count(MobilityTrip.id).label('count'),
        func.avg(MobilityTrip.cost_amount).label('avg_price')
    ).filter(
        MobilityTrip.user_id == user_id
    ).group_by(
        MobilityTrip.origin_lat,
        MobilityTrip.origin_lon,
        MobilityTrip.destination_lat,
        MobilityTrip.destination_lon
    ).order_by(func.count(MobilityTrip.id).desc()).limit(10).all()
    
    return {
        "routes": [
            {
                "start": {"lat": r.origin_lat, "lon": r.origin_lon},
                "end": {"lat": r.destination_lat, "lon": r.destination_lon},
                "request_count": r.count,
                "average_price": round(r.avg_price, 2) if r.avg_price else 0
            }
            for r in routes
        ]
    }


@router.get("/provider-usage")
@limiter.limit("60/minute")
async def get_provider_usage(
    request: Request,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get provider usage statistics."""
    user_id = current_user.id
    
    # combine mobility and orders?
    # For now, just MobilityTrip
    
    provider_stats = db.query(
        MobilityTrip.provider,
        func.count(MobilityTrip.id).label('count')
    ).filter(
        MobilityTrip.user_id == user_id
    ).group_by(MobilityTrip.provider).all()
    
    return {
        "providers": [
            {
                "provider": p.provider,
                "interaction_count": p.count
            }
            for p in provider_stats
        ]
    }
