from typing import Any, Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from core.authentication import get_current_user
from core.rate_limiting import limiter
from models.database import get_db
from models.models import User, Recommendation

router = APIRouter(prefix="", tags=["Home"])

@router.get("/recommendations", summary="Get recommendations")
@limiter.limit("15/minute")
async def get_recommendations(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Return a list of recommended items for the current user."""
    from models.models import VivIndex
    latest_index = db.query(VivIndex).filter(VivIndex.user_id == current_user.id).order_by(VivIndex.timestamp.desc()).first()
    
    recs = []
    if latest_index:
        if latest_index.financial_score and latest_index.financial_score < 40:
            recs.append({"title": "Review your spending", "description": "Your financial score is low. Let's look at where you can cut back.", "action": "Review Finances", "icon": "trending-down"})
        elif latest_index.financial_score and latest_index.financial_score >= 80:
             recs.append({"title": "Invest surplus cash", "description": "You have strong cash flow! Consider moving savings into investments.", "action": "View Options", "icon": "trending-up"})
             
        if latest_index.health_score and latest_index.health_score < 40:
             recs.append({"title": "Schedule a workout", "description": "Your health metrics dropped slightly this week.", "action": "Book Gym", "icon": "activity"})
             
        if latest_index.time_score and latest_index.time_score < 40:
             recs.append({"title": "Block focus time", "description": "Your schedule is very fragmented today.", "action": "Optimize Calendar", "icon": "clock"})

    if not recs:
        recs.append({"title": "All caught up!", "description": "No new recommendations at this time. Keep up the good work.", "action": None, "icon": "check-circle"})

    return {"items": recs}

@router.get("/treats", summary="Get treats")
@limiter.limit("15/minute")
async def get_treats(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Return a list of treats for the current user."""
    from models.models import VivIndex
    latest_index = db.query(VivIndex).filter(VivIndex.user_id == current_user.id).order_by(VivIndex.timestamp.desc()).first()
    
    treats = []
    if latest_index and latest_index.financial_score and latest_index.financial_score > 60:
         treats.append({"title": "Treat yourself to a nice dinner", "description": "You've stayed under budget this week!", "cost": 150, "icon": "coffee"})
    if latest_index and latest_index.time_score and latest_index.time_score > 70:
         treats.append({"title": "Take a half day off", "description": "You've been incredibly productive. You've earned a break.", "cost": 0, "icon": "sun"})
         
    return {"items": treats}

@router.get("/users/{user_id}/recommendations", summary="Get user recommendations")
async def get_user_recommendations(
    user_id: str,
    type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict[str, Any]:
    """Return stored recommendations for a user."""
    from fastapi import HTTPException
    if current_user.id != user_id:
         raise HTTPException(status_code=403, detail="Not authorized")
    
    query = db.query(Recommendation).filter(Recommendation.user_id == user_id)
    if type:
        query = query.filter(Recommendation.type == type)
    
    recs = query.order_by(Recommendation.timestamp.desc()).all()
    
    return {"data": recs}
