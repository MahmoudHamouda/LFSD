"""
Growth Dependencies - Entitlement checks for FastAPI routes.

Provides reusable dependencies for enforcing subscription limits.
"""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.database import get_db
from models.models import User, LifeGoal
from services.growth_service import GrowthService
from core.authentication import get_current_user


def check_goal_limit(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> None:
    """
    Dependency to check if user can create more goals based on their subscription.
    
    Raises HTTPException 429 if limit reached.
    """
    try:
        # Get user entitlements
        entitlements = GrowthService.get_entitlements(current_user.id, db)
        
        if not entitlements or not entitlements.limits:
            # No entitlements found - fail closed to free tier
            limit = 5
        else:
            # Safely extract limit with fallback
            limits_dict = entitlements.limits if isinstance(entitlements.limits, dict) else {}
            limit = limits_dict.get("goals", 5)  # Default to free tier
        
        # Check for unlimited
        if limit == -1:
            return  # Unlimited
        
        # Ensure limit is int (in case it came from JSON as string)
        limit = int(limit)
        
        # Count active goals (exclude soft-deleted if you have that column)
        current_count = (
            db.query(func.count(LifeGoal.id))
            .filter(LifeGoal.user_id == current_user.id)
            # .filter(LifeGoal.deleted_at == None)  # Uncomment if you have soft deletes
            .scalar()
        )
        
        if current_count >= limit:
            # Get next plan suggestion from entitlements
            current_plan = getattr(entitlements, 'plan_id', 'FREE')
            next_plan = _get_next_plan(current_plan)
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "message": f"You have reached your limit of {limit} goals.",
                    "current_count": current_count,
                    "limit": limit,
                    "suggested_action": f"Upgrade to {next_plan} for more goals." if next_plan else "Contact support for higher limits."
                }
            )
    
    except HTTPException:
        # Re-raise quota errors
        raise
    except Exception as e:
        # Log error and fail open (don't block user on entitlement errors)
        print(f"Error checking goal limit: {e}")
        # In production, you might want to fail closed instead
        return


def _get_next_plan(current_plan: str) -> str:
    """Get suggested upgrade plan."""
    upgrade_path = {
        "tier_free": "Basic",
        "tier_basic": "Pro",
        "tier_pro": "Enterprise",
    }
    return upgrade_path.get(current_plan, "Pro")
