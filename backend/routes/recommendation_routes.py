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
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Return a list of recommended items for the current user."""
    from models.models import VivIndex

    latest_index = (
        db.query(VivIndex)
        .filter(VivIndex.user_id == current_user.id)
        .order_by(VivIndex.timestamp.desc())
        .first()
    )

    recs = []
    if latest_index:
        if latest_index.financial_score and latest_index.financial_score < 40:
            recs.append(
                {
                    "id": "rec-1",
                    "type": "finance",
                    "title": "Review your spending",
                    "body": "Your financial score is low. Let's look at where you can cut back.",
                    "cta": {"label": "Review Finances", "href": "/finance"},
                    "icon": "trending-down",
                }
            )
        elif latest_index.financial_score and latest_index.financial_score >= 80:
            recs.append(
                {
                    "id": "rec-2",
                    "type": "finance",
                    "title": "Invest surplus cash",
                    "body": "You have strong cash flow! Consider moving savings into investments.",
                    "cta": {"label": "View Options", "href": "/finance"},
                    "icon": "trending-up",
                }
            )

        if latest_index.health_score and latest_index.health_score < 40:
            recs.append(
                {
                    "id": "rec-3",
                    "type": "health",
                    "title": "Schedule a workout",
                    "body": "Your health metrics dropped slightly this week.",
                    "cta": {"label": "Book Gym", "href": "/health"},
                    "icon": "activity",
                }
            )

        if latest_index.time_score and latest_index.time_score < 40:
            recs.append(
                {
                    "id": "rec-4",
                    "type": "time",
                    "title": "Block focus time",
                    "body": "Your schedule is very fragmented today.",
                    "cta": {"label": "Optimize Calendar", "href": "/time"},
                    "icon": "clock",
                }
            )

    if not recs:
        recs.append(
            {
                "id": "rec-ok",
                "type": "general",
                "title": "All caught up!",
                "body": "No new recommendations at this time. Keep up the good work.",
                "cta": {"label": "Dashboard", "href": "/"},
                "icon": "check-circle",
            }
        )

    return {"items": recs}


@router.get("/treats", summary="Get treats")
@limiter.limit("15/minute")
async def get_treats(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Return a list of treats for the current user."""
    from models.models import VivIndex

    latest_index = (
        db.query(VivIndex)
        .filter(VivIndex.user_id == current_user.id)
        .order_by(VivIndex.timestamp.desc())
        .first()
    )

    treats = []
    if (
        latest_index
        and latest_index.financial_score
        and latest_index.financial_score > 60
    ):
        treats.append(
            {
                "id": "treat-1",
                "category": "Dining",
                "title": "Treat yourself to a nice dinner",
                "body": "You've stayed under budget this week!",
                "cost": 150,
                "icon": "coffee",
                "cta": {"label": "View Treats", "href": "/"},
            }
        )
    if latest_index and latest_index.time_score and latest_index.time_score > 70:
        treats.append(
            {
                "id": "treat-2",
                "category": "Relaxation",
                "title": "Take a half day off",
                "body": "You've been incredibly productive. You've earned a break.",
                "cost": 0,
                "icon": "sun",
                "cta": {"label": "View Treats", "href": "/"},
            }
        )

    return {"items": treats}


@router.get("/users/{user_id}/recommendations", summary="Get user recommendations")
async def get_user_recommendations(
    user_id: str,
    type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
