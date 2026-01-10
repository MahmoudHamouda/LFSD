
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from models.database import get_db
from models.models import User, LifeGoal, FinancialAccount, FinancialScore
from models.api_models import GoalCreate, GoalUpdate, GoalResponse, GoalType
from core.authentication import get_current_user
from dependencies.growth_dependencies import check_goal_limit

router = APIRouter(prefix="/finance/goals", tags=["finance-goals"])

@router.get("", response_model=List[GoalResponse])
async def list_goals(
    pillar: Optional[str] = None,
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """List all life goals."""
    query = db.query(LifeGoal).filter(LifeGoal.user_id == current_user.id)
    if pillar:
        query = query.filter(LifeGoal.pillar == pillar)
    goals = query.all()
    return [
        GoalResponse(
            id=g.id,
            title=g.title,
            target_amount=g.target_amount,
            target_date=g.target_date,
            type=g.type or "custom",
            monthly_contribution_target=g.monthly_contribution_target or 0,
            priority=g.priority or "medium",
            saved_amount=g.saved_amount or 0,
            pillar=g.pillar or "finance",
            impact_vector_json=g.impact_vector_json
        ) for g in goals
    ]

@router.post("", response_model=GoalResponse)
async def create_goal(
    payload: GoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    entitlement_check: bool = Depends(check_goal_limit)
):
    """Create a new life goal."""
    import uuid
    new_goal = LifeGoal(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        title=payload.title,
        target_amount=payload.target_amount,
        target_date=payload.target_date,
        type=payload.type,
        pillar=payload.pillar,
        monthly_contribution_target=payload.monthly_contribution_target,
        priority=payload.priority,
        saved_amount=0 # Start at 0
    )
    db.add(new_goal)
    db.commit()
    db.refresh(new_goal)
    
    return GoalResponse(**new_goal.__dict__)

@router.patch("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: str,
    payload: GoalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a goal."""
    goal = db.query(LifeGoal).filter(LifeGoal.id == goal_id, LifeGoal.user_id == current_user.id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(goal, key, value)
        
    db.commit()
    db.refresh(goal)
    return GoalResponse(**goal.__dict__)

@router.delete("/{goal_id}")
async def delete_goal(
    goal_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a goal."""
    goal = db.query(LifeGoal).filter(LifeGoal.id == goal_id, LifeGoal.user_id == current_user.id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
        
    db.delete(goal)
    db.commit()
    return {"message": "Goal deleted"}

@router.get("/insights")
async def get_goal_insights(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculate gap between required savings for goals vs actual savings capability.
    """
    goals = db.query(LifeGoal).filter(LifeGoal.user_id == current_user.id).all()
    
    # Get latest financial snapshot for savings capability
    latest_score = db.query(FinancialScore).filter(FinancialScore.user_id == current_user.id)\
                     .order_by(FinancialScore.timestamp.desc()).first()
                     
    current_monthly_savings = latest_score.total_monthly_savings if latest_score else 0
    current_monthly_invest = 0 # If we had separate invest flow
    total_capacity = current_monthly_savings
    
    insights = []
    
    for g in goals:
        if not g.target_date or not g.target_amount:
            continue
            
        # Calculate months remaining
        now = datetime.utcnow()
        if g.target_date <= now:
            months_left = 0
        else:
            delta = g.target_date - now
            months_left = delta.days / 30.0
            
        remaining_amount = max(0, g.target_amount - (g.saved_amount or 0))
        
        if months_left > 0:
            required_monthly = remaining_amount / months_left
        else:
            required_monthly = remaining_amount # Due now
            
        gap = required_monthly - total_capacity
        
        insights.append({
            "goal_id": g.id,
            "goal_title": g.title,
            "required_monthly": round(required_monthly, 2),
            "current_capacity": round(total_capacity, 2),
            "gap": round(gap, 2),
            "status": "on_track" if gap <= 0 else "at_risk"
        })
        
    return {"goals": insights, "total_capacity": total_capacity}
