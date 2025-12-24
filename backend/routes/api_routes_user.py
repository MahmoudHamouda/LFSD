"""
User API Routes

Endpoints for user data management including profile, financial data,
engagement metrics, and calculated indexes.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import json

from models.database import get_db
from models.models import DBUser, DBFinancial
from models.models_health import DBUserIndex, DBHealthConnection, DBHealthMetric
from pydantic import BaseModel

router = APIRouter(prefix="/api/user", tags=["user"])

# ============================================================================
# Pydantic Models
# ============================================================================

class UserIdentity(BaseModel):
    id: str
    username: str
    email: str
    avatar: Optional[str] = None
    locale: str = "en-US"
    timezone: str = "UTC"

class AffordabilityMetrics(BaseModel):
    discretionaryIncome: float
    savingsRate: float
    debtToIncomeRatio: float

class UserFinancialProfile(BaseModel):
    income: float
    expenses: float
    savings: float
    debts: float
    currentMonthSpending: float
    affordabilityMetrics: AffordabilityMetrics

class HealthConnection(BaseModel):
    provider: str
    status: str
    connectedAt: Optional[str] = None
    lastSyncedAt: Optional[str] = None
    permissions: list[str] = []
    errorMessage: Optional[str] = None

class HealthMetrics(BaseModel):
    sleepScore: Optional[float] = None
    recovery: Optional[float] = None
    activityLoad: Optional[float] = None
    hrv: Optional[float] = None
    steps: Optional[int] = None

class UserHealthProfile(BaseModel):
    connections: list[HealthConnection]
    metrics: HealthMetrics
    hasAnyConnection: bool

class UserStreaks(BaseModel):
    dailyCheckIn: int = 0
    financialReview: int = 0

class UserEngagementProfile(BaseModel):
    lastActive: str
    streaks: UserStreaks
    mostUsedJourneys: list[str] = []

class IndexTrend(BaseModel):
    financialWellbeing: float = 0.0
    timeSaved: float = 0.0
    balance: Optional[float] = None

class UserIndexes(BaseModel):
    financialWellbeingIndex: float
    timeSavedIndex: float
    balanceIndex: Optional[float] = None
    trend: IndexTrend
    lastCalculatedAt: str

class User(BaseModel):
    identity: UserIdentity
    financial: UserFinancialProfile
    health: UserHealthProfile
    engagement: UserEngagementProfile
    indexes: UserIndexes

class UserUpdateRequest(BaseModel):
    identity: Optional[dict] = None
    financial: Optional[dict] = None
    engagement: Optional[dict] = None

# ============================================================================
# Helper Functions
# ============================================================================

def calculate_affordability_metrics(financial: DBFinancial) -> AffordabilityMetrics:
    """Calculate affordability metrics from financial data."""
    discretionary_income = financial.income - financial.expenses
    savings_rate = (financial.savings / financial.income * 100) if financial.income > 0 else 0
    debt_to_income = (financial.debts / financial.income * 100) if financial.income > 0 else 0
    
    return AffordabilityMetrics(
        discretionaryIncome=discretionary_income,
        savingsRate=round(savings_rate, 2),
        debtToIncomeRatio=round(debt_to_income, 2)
    )

def get_health_connections(user_id: str, db: Session) -> list[HealthConnection]:
    """Get all health connections for a user."""
    connections = db.query(DBHealthConnection).filter(
        DBHealthConnection.user_id == user_id
    ).all()
    
    return [
        HealthConnection(
            provider=conn.provider,
            status=conn.status,
            connectedAt=conn.connected_at.isoformat() if conn.connected_at else None,
            lastSyncedAt=conn.last_synced_at.isoformat() if conn.last_synced_at else None,
            permissions=json.loads(conn.permissions) if conn.permissions else [],
            errorMessage=conn.error_message
        )
        for conn in connections
    ]

def get_latest_health_metrics(user_id: str, db: Session) -> HealthMetrics:
    """Get latest health metrics for a user."""
    metrics = {}
    
    for metric_type in ['sleep', 'recovery', 'activity', 'hrv', 'steps']:
        latest = db.query(DBHealthMetric).filter(
            DBHealthMetric.user_id == user_id,
            DBHealthMetric.metric_type == metric_type
        ).order_by(DBHealthMetric.timestamp.desc()).first()
        
        if latest:
            if metric_type == 'sleep':
                metrics['sleepScore'] = latest.value
            elif metric_type == 'recovery':
                metrics['recovery'] = latest.value
            elif metric_type == 'activity':
                metrics['activityLoad'] = latest.value
            elif metric_type == 'hrv':
                metrics['hrv'] = latest.value
            elif metric_type == 'steps':
                metrics['steps'] = int(latest.value)
    
    return HealthMetrics(**metrics)

def get_user_indexes(user_id: str, db: Session) -> UserIndexes:
    """Get latest calculated indexes for a user."""
    latest_index = db.query(DBUserIndex).filter(
        DBUserIndex.user_id == user_id
    ).order_by(DBUserIndex.calculated_at.desc()).first()
    
    if not latest_index:
        # Return default indexes if none exist
        return UserIndexes(
            financialWellbeingIndex=50.0,
            timeSavedIndex=50.0,
            balanceIndex=None,
            trend=IndexTrend(),
            lastCalculatedAt=datetime.utcnow().isoformat()
        )
    
    return UserIndexes(
        financialWellbeingIndex=latest_index.financial_wellbeing,
        timeSavedIndex=latest_index.time_saved,
        balanceIndex=latest_index.balance_index,
        trend=IndexTrend(
            financialWellbeing=latest_index.trend_financial,
            timeSaved=latest_index.trend_time_saved,
            balance=latest_index.trend_balance
        ),
        lastCalculatedAt=latest_index.calculated_at.isoformat()
    )

# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/me")
async def get_current_user(db: Session = Depends(get_db)):
    """
    Get current user data including all profiles and indexes.
    
    Returns complete user object with:
    - Identity (profile info)
    - Financial profile with affordability metrics
    - Health connections and metrics
    - Engagement profile
    - Calculated indexes
    """
    # For now, using a default user ID (in production, get from auth token)
    user_id = "default_user"
    
    # Get user from models.database
    db_user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get financial data
    db_financial = db.query(DBFinancial).filter(DBFinancial.user_id == user_id).first()
    if not db_financial:
        raise HTTPException(status_code=404, detail="Financial data not found")
    
    # Build user object
    user = User(
        identity=UserIdentity(
            id=db_user.id,
            username=db_user.username,
            email=db_user.email,
            avatar=None,
            locale="en-US",
            timezone="UTC"
        ),
        financial=UserFinancialProfile(
            income=db_financial.income or 0,
            expenses=db_financial.expenses or 0,
            savings=db_financial.savings or 0,
            debts=db_financial.debts or 0,
            currentMonthSpending=db_financial.expenses or 0,
            affordabilityMetrics=calculate_affordability_metrics(db_financial)
        ),
        health=UserHealthProfile(
            connections=get_health_connections(user_id, db),
            metrics=get_latest_health_metrics(user_id, db),
            hasAnyConnection=len(get_health_connections(user_id, db)) > 0
        ),
        engagement=UserEngagementProfile(
            lastActive=datetime.utcnow().isoformat(),
            streaks=UserStreaks(dailyCheckIn=0, financialReview=0),
            mostUsedJourneys=[]
        ),
        indexes=get_user_indexes(user_id, db)
    )
    
    return {"user": user, "timestamp": datetime.utcnow().isoformat()}

@router.patch("/me")
async def update_current_user(
    updates: UserUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update current user data.
    
    Accepts partial updates for:
    - identity (locale, timezone, etc.)
    - financial (income, expenses, savings, debts)
    - engagement (preferences, etc.)
    """
    user_id = "default_user"
    
    db_user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update identity fields
    if updates.identity:
        if 'username' in updates.identity:
            db_user.username = updates.identity['username']
        if 'email' in updates.identity:
            db_user.email = updates.identity['email']
    
    # Update financial fields
    if updates.financial:
        db_financial = db.query(DBFinancial).filter(DBFinancial.user_id == user_id).first()
        if db_financial:
            if 'income' in updates.financial:
                db_financial.income = updates.financial['income']
            if 'expenses' in updates.financial:
                db_financial.expenses = updates.financial['expenses']
            if 'savings' in updates.financial:
                db_financial.savings = updates.financial['savings']
            if 'debts' in updates.financial:
                db_financial.debts = updates.financial['debts']
    
    db.commit()
    
    # Return updated user
    return await get_current_user(db)
