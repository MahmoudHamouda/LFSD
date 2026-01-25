"""
Index API Routes
from core.authentication import get_current_user
from models.models import User

Endpoints for calculating and retrieving user wellbeing indexes.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from models.database import get_db
from services.index_calculator_service import calculate_user_indexes

router = APIRouter(prefix="/api/indexes", tags=["indexes"])

# ============================================================================
# Pydantic Models
# ============================================================================

class IndexTrend(BaseModel):
    financialWellbeing: float
    timeSaved: float
    balance: float | None

class UserIndexes(BaseModel):
    financialWellbeingIndex: float
    timeSavedIndex: float
    balanceIndex: float | None
    trend: IndexTrend
    lastCalculatedAt: str

# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/calculate")
async def calculate_indexes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculate user wellbeing indexes.
    
    Calculates:
    - Financial Wellbeing Index (0-100)
    - Time Saved Index (0-100)
    - Balance Index (0-100, health-enhanced)
    
    Stores results in database and returns calculated values with trends.
    """
    user_id = current_user.id
    
    
    try:
        indexes = calculate_user_indexes(user_id, db)
        return {"indexes": indexes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate indexes: {str(e)}")

@router.get("/current")
async def get_current_indexes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get current user indexes without recalculating.
    
    Returns the most recently calculated indexes.
    """
    user_id = current_user.id
    
    from models.models import VivIndex
    
    latest = db.query(VivIndex).filter(
        VivIndex.user_id == user_id
    ).order_by(VivIndex.timestamp.desc()).first()
    
    if not latest:
        # Calculate if no indexes exist
        return await calculate_indexes(db, current_user)
    
    return {
        "indexes": {
        "indexes": {
            "financialWellbeingIndex": latest.financial_score,
            "timeSavedIndex": latest.time_score,
            "balanceIndex": latest.health_score,
            "trend": {
                "financialWellbeing": 0.0,
                "timeSaved": 0.0,
                "balance": 0.0
            },
            "lastCalculatedAt": latest.timestamp.isoformat()
        }
        }
    }
