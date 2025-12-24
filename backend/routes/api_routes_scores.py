"""
API Routes for User Scores
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

import uuid
import json
from datetime import datetime

from models.database import get_db
from models.models import User, VivIndex, FinancialScore
from services.time_scoring import calculate_productivity_score
from services.financial_scoring import calculate_financial_health_score
from services.health_scoring import calculate_health_score
from datetime import timedelta

router = APIRouter()

from models.api_models import OnboardingPayload
from core.authentication import get_current_user


class ScoreResponse(BaseModel):
    financial_score: float
    health_score: float
    productivity_score: float
    financial_trend: Optional[float] = None
    health_trend: Optional[float] = None
    productivity_trend: Optional[float] = None
    has_data: bool = True
    breakdown: Dict[str, Any]
    categories: Optional[Dict[str, Any]] = {}



@router.post("/onboarding")
async def submit_onboarding(payload: OnboardingPayload, db: Session = Depends(get_db)):
    """
    Process onboarding data, calculate scores, and save to DB.
    """
    try:
        user_id = payload.user_id or "default_user" 
        
        # 1. Get or Create User (Must exist for Foreign Keys)
        print(f"DEBUG: Fetching user {user_id}...")
        # Check by ID first
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            # Fallback for default user creation if not found
            if user_id == "default_user":
                print("DEBUG: User not found by ID, checking email...")
                user_by_email = db.query(User).filter(User.email == "default@example.com").first()
                if user_by_email:
                    user = user_by_email
                    user_id = user.id
                else:
                    print("DEBUG: Creating new default user...")
                    user = User(id=user_id, email="default@example.com", hashed_password="hashed")
                    db.add(user)
                    db.commit()
            else:
                 # If a specific user_id was provided (e.g. from signup) but not found, 
                 # it might be a timing issue or invalid ID. 
                 # For now, we'll log it and fallback to default or fail? 
                 # Let's assume if it's passed it should exist. 
                 print(f"DEBUG: Warning - User {user_id} not found. Creating placeholder.")
                 # Create user placeholder if needed (though signup should have handled it)
                 try:
                     user = User(id=user_id, email=f"{user_id}@temp.com", hashed_password="hashed")
                     db.add(user)
                     db.commit()
                 except Exception:
                     db.rollback()
                     user = db.query(User).filter(User.id == user_id).first()

        print(f"DEBUG: User active: {user_id}")
        
        # 2. Calculate Scores
        
        # If manual mode is explicitly requested, clear existing transactions for default_user
        if payload.is_manual_mode and user_id == "default_user":
            print("DEBUG: Clearing transactions for manual mode...")
            from models.models import Transaction, Statement
            db.query(Transaction).filter(Transaction.user_id == user_id).delete()
            db.query(Statement).filter(Statement.user_id == user_id).delete()
            db.commit()

        print("DEBUG: Calculating Financial Score...")
        # Use the new 8-pillar financial scoring engine
        financial_data = calculate_financial_health_score(
            user_id, 
            payload.dict(), 
            db, 
            is_manual_mode=payload.is_manual_mode
        )
        print("DEBUG: Financial Score Done.")
        
        print("DEBUG: Calculating Health Score...")
        hs_data = calculate_health_score(user_id, payload.dict(), db)
        print("DEBUG: Health Score Done.")

        print("DEBUG: Calculating Productivity Score...")
        tes_data = calculate_productivity_score(user_id, payload.dict(), db)
        print("DEBUG: Productivity Score Done.")
        
        # Re-fetch user to ensure attached to session after previous commits
        user = db.query(User).filter(User.id == user_id).first()
        
        # 3. Save Scores to VivIndex (High Level)
        print("DEBUG: Saving VivIndex...")
        viv_index = VivIndex(
            id=str(uuid.uuid4()),
            user_id=user_id,
            financial_score=financial_data["overall_score"],
            health_score=hs_data["score"],
            time_score=tes_data["score"],
            snapshot_reason="Onboarding",
            timestamp=datetime.utcnow()
        )
        db.add(viv_index)
        
        # 4. Save Breakdown to User Profile
        print("DEBUG: Saving Profile...")
        profile = user.profile_json or {}
        profile["onboarding_breakdown"] = {
            "financial": financial_data,
            "health": hs_data,
            "productivity": tes_data
        }
        # Save full onboarding data
        profile["onboarding_data"] = payload.dict()
        
        user.profile_json = profile
        
        db.commit()
        print("DEBUG: Commit successful.")
        
        return ScoreResponse(
            financial_score=viv_index.financial_score,
            health_score=viv_index.health_score,
            productivity_score=viv_index.time_score,
            has_data=True,
            breakdown=profile["onboarding_breakdown"]
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"CRITICAL ONBOARDING ERROR: {e}")
        # FAIL SAFE: Return 0s instead of crashing
        return ScoreResponse(
            financial_score=0,
            health_score=0,
            productivity_score=0,
            has_data=False,
            breakdown={"error": str(e)}
        )

@router.get("/current")
async def get_scores(
    period: str = "week",
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Get current user scores and trends.
    period: 'week' (compare vs 7 days ago) or 'month' (compare vs 30 days ago)
    """
    user_id = current_user.id
    
    # Get latest VivIndex
    latest_index = db.query(VivIndex).filter(VivIndex.user_id == user_id).order_by(VivIndex.timestamp.desc()).first()
    
    if not latest_index:
        return ScoreResponse(
            financial_score=0,
            health_score=0,
            productivity_score=0,
            financial_trend=None,
            health_trend=None,
            productivity_trend=None,
            has_data=False,
            breakdown={}
        )

    # Calculate Trends
    days_back = 30 if period == "month" else 7
    cutoff_date = datetime.utcnow() - timedelta(days=days_back)
    
    # Find the snapshot closest to cutoff (must be before or at cutoff)
    # Ideally, we want the first snapshot *after* the cutoff, or the last one *before*?
    # Actually, we want the score from `days_back` ago. So we look for the latest record that is <= cutoff.
    # Logic: sort desc by timestamp, filter where timestamp <= cutoff, take first.
    historical_index = db.query(VivIndex).filter(
        VivIndex.user_id == user_id,
        VivIndex.timestamp <= cutoff_date
    ).order_by(VivIndex.timestamp.desc()).first()

    fin_trend = None
    hlth_trend = None
    prod_trend = None

    if historical_index:
        fin_trend = latest_index.financial_score - historical_index.financial_score
        hlth_trend = latest_index.health_score - historical_index.health_score
        prod_trend = latest_index.time_score - historical_index.time_score
        
    # Get breakdown from profile
    user = db.query(User).filter(User.id == user_id).first()
    breakdown = {}
    if user and user.profile_json:
        breakdown = user.profile_json.get("onboarding_breakdown", {})

    # Fallback to FinancialScore table if profile breakdown is missing/incomplete for financial data
    if not breakdown.get("financial"):
        latest_fs = db.query(FinancialScore).filter(FinancialScore.user_id == user_id).order_by(FinancialScore.timestamp.desc()).first()
        if latest_fs:
            print(f"DEBUG: Recovering financial breakdown from FinancialScore table for user {user_id}")
            breakdown["financial"] = {
                "overall_score": latest_fs.overall_score,
                "subscores": {
                    "cashflow_stability": latest_fs.cashflow_stability_score,
                    "bills_coverage": latest_fs.bills_coverage_score,
                    "savings_rate": latest_fs.savings_rate_score,
                    "debt_load": latest_fs.debt_load_score,
                    "discretionary_control": latest_fs.discretionary_control_score,
                    "emergency_buffer": latest_fs.emergency_buffer_score,
                    "networth_momentum": latest_fs.networth_momentum_score,
                    "investment_health": latest_fs.investment_health_score
                },
                "metadata": {
                     "time_window": latest_fs.time_window,
                     "data_sources": latest_fs.data_sources_json
                }
            }
        
    # Construct Categories for Frontend Compatibility (flattened subscores)
    categories = {}
    if breakdown.get("financial") and breakdown["financial"].get("subscores"):
        for key, val in breakdown["financial"]["subscores"].items():
            categories[key] = {"score": val, "badge": "Neutral"} # Default badge

    return ScoreResponse(
        financial_score=latest_index.financial_score,
        health_score=latest_index.health_score,
        productivity_score=latest_index.time_score,
        financial_trend=round(fin_trend, 1) if fin_trend is not None else None,
        health_trend=round(hlth_trend, 1) if hlth_trend is not None else None,
        productivity_trend=round(prod_trend, 1) if prod_trend is not None else None,
        breakdown=breakdown,
        categories=categories
    )

@router.get("/users/{user_id}/financial-score")
async def get_financial_score_details(user_id: str, db: Session = Depends(get_db)):
    """
    Get detailed financial score breakdown.
    """
    # For now, we are using "default_user" in the onboarding flow, 
    # but this endpoint supports specific user_id if needed.
    if user_id == "me":
        user_id = "default_user"
        
    latest_score = db.query(FinancialScore).filter(FinancialScore.user_id == user_id).order_by(FinancialScore.timestamp.desc()).first()
    
    if not latest_score:
        raise HTTPException(status_code=404, detail="Financial score not found")
        
    return {
        "overall_score": latest_score.overall_score,
        "subscores": {
            "income_stability": latest_score.income_stability_score,
            "burn_rate": latest_score.burn_rate_score,
            "savings_momentum": latest_score.savings_momentum_score,
            "debt_stress": latest_score.debt_stress_score,
            "recurring_commitments": latest_score.recurring_commitments_score,
            "spending_stability": latest_score.spending_stability_score,
            "liquidity_cushion": latest_score.liquidity_cushion_score,
            "risk_indicators": latest_score.risk_indicator_score
        },
        "time_window": latest_score.time_window,
        "data_sources": latest_score.data_sources_json
    }
