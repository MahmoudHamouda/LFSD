"""
Index API Routes

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
async def calculate_indexes(db: Session = Depends(get_db)):
    """
    Calculate user wellbeing indexes.
    
    Calculates:
    - Financial Wellbeing Index (0-100)
    - Time Saved Index (0-100)
    - Balance Index (0-100, health-enhanced)
    
    Stores results in database and returns calculated values with trends.
    """
    user_id = "default_user"
    
    try:
        indexes = calculate_user_indexes(user_id, db)
        return {"indexes": indexes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate indexes: {str(e)}")

@router.get("/current")
async def get_current_indexes(db: Session = Depends(get_db)):
    """
    Get current user indexes without recalculating.
    
    Returns the most recently calculated indexes.
    """
    user_id = "default_user"
    
    from models.models_health import DBUserIndex
    
    latest = db.query(DBUserIndex).filter(
        DBUserIndex.user_id == user_id
    ).order_by(DBUserIndex.calculated_at.desc()).first()
    
    if not latest:
        # Calculate if no indexes exist
        return await calculate_indexes(db)
    
    return {
        "indexes": {
            "financialWellbeingIndex": latest.financial_wellbeing,
            "timeSavedIndex": latest.time_saved,
            "balanceIndex": latest.balance_index,
            "trend": {
                "financialWellbeing": latest.trend_financial,
                "timeSaved": latest.trend_time_saved,
                "balance": latest.trend_balance
            },
            "lastCalculatedAt": latest.calculated_at.isoformat()
        }
    }
