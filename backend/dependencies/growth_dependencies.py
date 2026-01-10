from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from models.database import get_db
from models.models import User, LifeGoal
from services.growth_service import GrowthService, PlanId
from core.authentication import get_current_user

def check_goal_limit(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Dependency to enforce goal creation limits based on subscription plan.
    Raises 403 if limit is reached.
    """
    entitlements = GrowthService.get_entitlements(current_user.id, db)
    limit = entitlements.limits.get("goals", 5) # Default to 5 if missing
    
    if limit == -1: # Unlimited
        return True
        
    current_count = db.query(LifeGoal).filter(LifeGoal.user_id == current_user.id).count()
    
    if current_count >= limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "LIMIT_REACHED",
                "message": f"You have reached your limit of {limit} goals. Upgrade to Pro for unlimited goals.",
                "limit": limit,
                "current": current_count
            }
        )
    return True
