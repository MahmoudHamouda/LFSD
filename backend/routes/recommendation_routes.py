from typing import Any, Optional
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from core.authentication import get_current_user
from core.rate_limiting import limiter
from models.database import get_db
from models.models import User, Recommendation
from services.recommendation_service.recommendation_engine import compute_recommendations
from services.recommendation_service.treat_engine import compute_treats

router = APIRouter(prefix="", tags=["Home"])

@router.get("/recommendations", summary="Get recommendations")
@limiter.limit("15/minute")
async def get_recommendations(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Return a list of recommended items for the current user."""
    items = compute_recommendations(current_user.id, db)
    return {"items": items}

@router.get("/treats", summary="Get treats")
@limiter.limit("15/minute")
async def get_treats(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    """Return a list of treats for the current user."""
    treats = compute_treats(current_user.id, db)
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
