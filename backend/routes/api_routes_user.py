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
from models.models import User, FinancialScore, HealthDailySummary, Connection, HealthDataSample, VivIndex
from core.authentication import get_current_user
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

def calculate_affordability_metrics(financial_score: FinancialScore) -> AffordabilityMetrics:
    """Calculate affordability metrics from financial data."""
    # Logic extracted from score if possible, or mocked for now since FinancialScore has scores not raw details except totals
    income = financial_score.total_monthly_income or 0
    expenses = financial_score.total_monthly_expenses or 0
    savings = financial_score.total_monthly_savings or 0
    # debts not directly in summary, using score inverse? or passed in.
    
    discretionary_income = income - expenses
    savings_rate = (savings / income * 100) if income > 0 else 0
    
    return AffordabilityMetrics(
        discretionaryIncome=discretionary_income,
        savingsRate=round(savings_rate, 2),
        debtToIncomeRatio=0.0 # Placeholder
    )

def get_health_connections(user_id: str, db: Session) -> list[HealthConnection]:
    """Get all health connections for a user."""
    connections = db.query(Connection).filter(
        Connection.user_id == user_id
    ).all()
    
    return [
        HealthConnection(
            provider=conn.provider,
            status=conn.status,
            connectedAt=conn.updated_at.isoformat() if conn.updated_at else None,
            lastSyncedAt=conn.updated_at.isoformat() if conn.updated_at else None,
            permissions=json.loads(conn.metadata_json).get("permissions", []) if conn.metadata_json else [],
            errorMessage=json.loads(conn.metadata_json or "{}").get("last_error")
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
    latest_index = db.query(VivIndex).filter(
        VivIndex.user_id == user_id
    ).order_by(VivIndex.timestamp.desc()).first()
    
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
        financialWellbeingIndex=latest_index.financial_score,
        timeSavedIndex=latest_index.time_score,
        balanceIndex=latest_index.health_score,
        trend=IndexTrend(), # No trend in VivIndex yet
        lastCalculatedAt=latest_index.timestamp.isoformat()
    )

# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/me")
async def get_user_profile(
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user data including all profiles and indexes.
    
    Returns complete user object with:
    - Identity (profile info)
    - Financial profile with affordability metrics
    - Health connections and metrics
    - Engagement profile
    - Calculated indexes
    """
    user_id = current_user.id
    
    # Get financial data (Score as proxy)
    db_financial = db.query(FinancialScore).filter(FinancialScore.user_id == user_id).order_by(FinancialScore.timestamp.desc()).first()
    if not db_financial:
        db_financial = FinancialScore(user_id=user_id) # Empty placeholder
    
    # Calculate Streaks
    # 1. Daily Check-in: Consecutive days with HealthDailySummary or VivLog
    # (Using HealthDailySummary as proxy for activity for now)
    summary_dates = db.query(HealthDailySummary.date).filter(
        HealthDailySummary.user_id == user_id
    ).order_by(HealthDailySummary.date.desc()).limit(30).all()
    
    check_in_streak = 0
    if summary_dates:
        import datetime as dt
        today = dt.date.today()
        dates = [d[0] for d in summary_dates]
        
        # Check if today or yesterday exists to start streak
        if today in dates or (today - dt.timedelta(days=1)) in dates:
            current = today
            # If today missing but yesterday present, start from yesterday
            if today not in dates:
                current = today - dt.timedelta(days=1)
            
            check_in_streak = 0
            # Iterate backwards
            while current in dates:
                check_in_streak += 1
                current -= dt.timedelta(days=1)
    
    # 2. Financial Review: Consecutive weeks with UserIndex
    index_count = db.query(VivIndex).filter(VivIndex.user_id == user_id).count()
    financial_streak = min(index_count, 52) # Cap at 52 weeks
    
    # Build user object
    user = User(
        identity=UserIdentity(
            id=current_user.id,
            username=current_user.username,
            email=current_user.email,
            avatar=None,
            locale="en-US",
            timezone="UTC"
        ),
        financial=UserFinancialProfile(
            income=db_financial.total_monthly_income or 0,
            expenses=db_financial.total_monthly_expenses or 0,
            savings=db_financial.total_monthly_savings or 0,
            debts=0, # Not in score yet
            currentMonthSpending=db_financial.total_monthly_expenses or 0,
            affordabilityMetrics=calculate_affordability_metrics(db_financial)
        ),
        health=UserHealthProfile(
            connections=get_health_connections(user_id, db),
            metrics=get_latest_health_metrics(user_id, db),
            hasAnyConnection=len(get_health_connections(user_id, db)) > 0
        ),
        engagement=UserEngagementProfile(
            lastActive=datetime.utcnow().isoformat(),
            streaks=UserStreaks(dailyCheckIn=check_in_streak, financialReview=financial_streak),
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
    user_id = current_user.id
    
    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update identity fields
    if updates.identity:
        if 'username' in updates.identity:
            db_user.username = updates.identity['username']
        if 'email' in updates.identity:
            db_user.email = updates.identity['email']
    
    # Update financial fields - (Requires Score update or Profile model - skipping for now as strict Profile model is missing)
    if updates.financial:
        pass # To be implemented with correct FinancialProfile model
    
    db.commit()
    
    # Return updated user
    return await get_current_user(db)
