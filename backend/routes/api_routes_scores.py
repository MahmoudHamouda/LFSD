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
from services.time_service import calculate_time_score
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
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"DEBUG: Fetching user {user_id}...")
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
            from models.models import FinancialTransaction, Statement
            db.query(FinancialTransaction).filter(FinancialTransaction.user_id == user_id).delete()
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
    import core.config
    settings = core.config.get_settings()
    try:
        user_id = current_user.id
        
        # Debug Info Injection (EARLY)
        count_viv = db.query(VivIndex).filter(VivIndex.user_id == user_id).count()
        debug_info = {
            "user_id": user_id,
            "viv_count": count_viv,
            "latest_index_found": False
        }
        # logger.debug(f"DEBUG_CLOUD_RUN: {debug_info}")

        # Get latest VivIndex
        latest_index = db.query(VivIndex).filter(VivIndex.user_id == user_id).order_by(VivIndex.timestamp.desc()).first()
        
        if not latest_index:
            return ScoreResponse(
                financial_score=0,
                health_score=0,
                productivity_score=0,
                has_data=False,
                breakdown={"debug_info": debug_info}
            )
        
        debug_info["latest_index_found"] = True

        # Calculate Trends
        days_back = 30 if period == "month" else 7
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        # ... (rest of logic) ...
        historical_index = db.query(VivIndex).filter(
            VivIndex.user_id == user_id,
            VivIndex.timestamp <= cutoff_date
        ).order_by(VivIndex.timestamp.desc()).first()

        fin_trend = None
        hlth_trend = None
        prod_trend = None

        if historical_index:
            # Safe subtraction handles None (though defaults should prevent it)
            current_fin = latest_index.financial_score or 50.0
            hist_fin = historical_index.financial_score or 50.0
            fin_trend = current_fin - hist_fin

            current_hlth = latest_index.health_score or 50.0
            hist_hlth = historical_index.health_score or 50.0
            hlth_trend = current_hlth - hist_hlth

            current_time = latest_index.time_score or 50.0
            hist_time = historical_index.time_score or 50.0
            prod_trend = current_time - hist_time
            
        # Get breakdown from profile
        user = db.query(User).filter(User.id == user_id).first()
        breakdown = {}
        if user and user.profile_json:
            breakdown = user.profile_json.get("onboarding_breakdown", {})

        # Fallback to FinancialScore table if profile breakdown is missing/incomplete for financial data
        try:
            if not breakdown.get("financial"):
                latest_fs = db.query(FinancialScore).filter(FinancialScore.user_id == user_id).order_by(FinancialScore.timestamp.desc()).first()
                if latest_fs:
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
        except Exception as e:
            print(f"WARNING: FinancialScore query failed: {e}")
            db.rollback()
            breakdown["debug_financial_error"] = str(e)
            import traceback
            breakdown["debug_financial_trace"] = traceback.format_exc()
            
        # Always prefer TimeScore table for productivity/time data if it exists
        try:
            from models.models import TimeScore
            latest_ts = db.query(TimeScore).filter(TimeScore.user_id == user_id).order_by(TimeScore.timestamp.desc()).first()
            if latest_ts:
                breakdown["productivity"] = {
                    "overall_score": latest_ts.overall_score,
                    "subscores": {
                        "schedule_coverage": latest_ts.schedule_coverage_score,
                        "planning_habit": latest_ts.planning_habit_score,
                        "focus_blocks": latest_ts.focus_blocks_score,
                        "meeting_load": latest_ts.meeting_load_score,
                        "context_switching": latest_ts.context_switching_score,
                        "weekly_rhythm": latest_ts.weekly_rhythm_score,
                        "time_alignment": latest_ts.time_alignment_score
                    },
                    "metadata": {
                        "time_window": latest_ts.time_window,
                        "data_sources": latest_ts.data_sources_json
                    }
                }
        except Exception as e:
            print(f"WARNING: TimeScore query failed: {e}")
            db.rollback()
            breakdown["debug_time_error"] = str(e)
            import traceback
            breakdown["debug_time_trace"] = traceback.format_exc()
            
        # Construct Categories for Frontend Compatibility (flattened subscores)
        categories = {}
        
        # Ensure base structures exist to prevent frontend React undefined crashes
        if "financial" not in breakdown or not breakdown["financial"]:
            breakdown["financial"] = {"overall_score": 0.0, "subscores": {}}
        if "health" not in breakdown or not breakdown["health"]:
            breakdown["health"] = {"overall_score": 0.0, "subscores": {}}
        if "productivity" not in breakdown or not breakdown["productivity"]:
            breakdown["productivity"] = {"overall_score": 0.0, "subscores": {}}
        elif "overall_score" not in breakdown["productivity"] and "score" in breakdown["productivity"]:
            # Preserve onboarding scores: onboarding saves under "score" key
            breakdown["productivity"]["overall_score"] = breakdown["productivity"]["score"]
        
        # Populate categories with subscores and coverage data based on available data
        # Financial subscores
        if breakdown.get("financial") and breakdown["financial"].get("subscores"):
            from models.models import FinancialTransaction
            
            # Calculate coverage for financial pillars (days with transaction data)
            window_days = 30
            start_date = datetime.utcnow() - timedelta(days=window_days)
            
            tx_dates = db.query(FinancialTransaction.transaction_date).filter(
                FinancialTransaction.user_id == user_id,
                FinancialTransaction.transaction_date >= start_date
            ).distinct().count()
            
            # All financial pillars share the same coverage (based on transaction data)
            coverage_days = tx_dates
            
            # Map each subscore to categories format
            subscores = breakdown["financial"]["subscores"]
            for pillar_id, score in subscores.items():
                categories[pillar_id] = {
                    "score": score,
                    "coverage": coverage_days
                }
        
        # Time/Productivity subscores (if user has time/productivity data)
        time_data = breakdown.get("productivity") or breakdown.get("time")
        if time_data and time_data.get("subscores"):
            from models.models import CalendarEvent
            
            # Calculate coverage for time pillars (days with calendar events)
            window_days = 30
            start_date = datetime.utcnow() - timedelta(days=window_days)
            
            event_dates = db.query(CalendarEvent.start_time).filter(
                CalendarEvent.user_id == user_id,
                CalendarEvent.start_time >= start_date
            ).distinct().count()
            
            coverage_days = event_dates
            
            # Map time subscores
            subscores = time_data["subscores"]
            for pillar_id, score in subscores.items():
                categories[pillar_id] = {
                    "score": score,
                    "coverage": coverage_days
                }
        
        # Health subscores (if user has health data)
        if breakdown.get("health") and breakdown["health"].get("subscores"):
            from models.models import HealthDailySummary
            
            # Calculate coverage for health pillars (days with health data)
            window_days = 30
            start_date = datetime.utcnow() - timedelta(days=window_days)
            
            health_dates = db.query(HealthDailySummary.date).filter(
                HealthDailySummary.user_id == user_id,
                HealthDailySummary.date >= start_date.date()
            ).distinct().count()
            
            coverage_days = health_dates
            
            # Map health subscores
            subscores = breakdown["health"]["subscores"]
            for pillar_id, score in subscores.items():
                categories[pillar_id] = {
                    "score": score,
                    "coverage": coverage_days
                }
        
        # Inject debug info into final breakdown only if DEBUG
        if settings.DEBUG:
            breakdown["debug_info"] = debug_info

        # Use productivity score from breakdown if available (from TimeScore), otherwise fallback to VivIndex
        productivity_score = latest_index.time_score
        if breakdown.get("productivity"):
            if breakdown["productivity"].get("overall_score"):
                productivity_score = breakdown["productivity"]["overall_score"]
            elif breakdown["productivity"].get("score"):
                productivity_score = breakdown["productivity"]["score"]
        elif breakdown.get("time"):
            if breakdown["time"].get("overall_score"):
                productivity_score = breakdown["time"]["overall_score"]
            elif breakdown["time"].get("score"):
                productivity_score = breakdown["time"]["score"]

        return ScoreResponse(
            financial_score=latest_index.financial_score,
            health_score=latest_index.health_score,
            productivity_score=productivity_score,
            financial_trend=round(fin_trend, 1) if fin_trend is not None else None,
            health_trend=round(hlth_trend, 1) if hlth_trend is not None else None,
            productivity_trend=round(prod_trend, 1) if prod_trend is not None else None,
            breakdown=breakdown,
            categories=categories
        )
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print(f"CRITICAL SCORE ERROR: {error_msg}")
        return ScoreResponse(
            financial_score=0,
            health_score=0,
            productivity_score=0,
            has_data=False,
            breakdown={"error_trace": error_msg},
            categories={}
        )

@router.get("/debug/schema")
async def debug_schema(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) # Only authenticated users (or admin)
):
    import core.config
    settings = core.config.get_settings()
    if not settings.DEBUG and getattr(current_user, "role", "user") != "admin":
        raise HTTPException(status_code=403, detail="Debug access forbidden")
    """
    Debug endpoint to inspect DB schema.
    """
    try:
        # Only allow admin or specific users
        # if current_user.role != "admin": raise HTTPException(403)
        
        from sqlalchemy import inspect
        inspector = inspect(db.get_bind())
        tables = inspector.get_table_names()
        
        time_columns = []
        if "time_scores" in tables:
            time_columns = [c["name"] for c in inspector.get_columns("time_scores")]
            
        return {
            "tables": tables,
            "time_scores_columns": time_columns
        }
    except Exception as e:
        return {"error": str(e)}

@router.post("/debug/fix_permissions")
async def debug_fix_permissions(db: Session = Depends(get_db)):
    """
    Attempt to grant permissions on time_scores to postgres user.
    """
    try:
        from sqlalchemy import text
        # Try specific table first
        db.execute(text("GRANT ALL PRIVILEGES ON TABLE time_scores TO postgres;"))
        # Also try sequence if it exists (for ID generation if auto-increment, though we use UUID strings usually)
        # db.execute(text("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;"))
        db.commit()
        return {"status": "success", "message": "Permissions granted on time_scores."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/debug/trigger_calc")
async def debug_trigger_calc(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Trigger complete calculation of scores (Finance, Health, Time) for current user.
    Populates FinancialScore, TimeScore, and VivIndex tables from raw data.
    """
    try:
        user_id = current_user.id
        # Clear any stale transaction (Cloud SQL pooled connections)
        try:
            db.rollback()
        except Exception:
            pass
        
        onboarding = current_user.profile_json if current_user.profile_json else {}
        fin_val = 50.0
        health_val = 50.0
        time_val = 50.0
        ts = None

        # 1. Time/Productivity Score — isolated
        try:
            from models.models import TimeScore
            ts = calculate_time_score(db, user_id, window_days=30)
            if ts:
                time_val = ts.overall_score
        except Exception as e:
            logger.warning(f"Time score calculation failed (continuing): {e}")
            try:
                db.rollback()
            except Exception:
                pass

        # 2. Financial Score — isolated
        try:
            fin_data = calculate_financial_health_score(user_id, onboarding, db)
            if fin_data:
                fin_val = fin_data.get("overall_score", 50.0)
        except Exception as e:
            logger.warning(f"Financial score calculation failed (continuing): {e}")
            try:
                db.rollback()
            except Exception:
                pass

        # 3. Health Score — isolated
        try:
            hs_data = calculate_health_score(user_id, onboarding, db)
            if hs_data:
                health_val = hs_data.get("score", 50.0)
        except Exception as e:
            logger.warning(f"Health score calculation failed (continuing): {e}")
            try:
                db.rollback()
            except Exception:
                pass

        # 4. Try to fetch persisted scores (may be better than computed)
        try:
            latest_fs = db.query(FinancialScore).filter(FinancialScore.user_id == user_id).order_by(FinancialScore.timestamp.desc()).first()
            if latest_fs:
                fin_val = latest_fs.overall_score
        except Exception:
            try:
                db.rollback()
            except Exception:
                pass

        try:
            from models.models import TimeScore
            latest_ts = db.query(TimeScore).filter(TimeScore.user_id == user_id).order_by(TimeScore.timestamp.desc()).first()
            if latest_ts:
                time_val = latest_ts.overall_score
        except Exception:
            try:
                db.rollback()
            except Exception:
                pass

        # 5. Always create a VivIndex snapshot
        try:
            db.rollback()  # ensure clean transaction
        except Exception:
            pass

        viv_index = VivIndex(
            id=str(uuid.uuid4()),
            user_id=user_id,
            financial_score=fin_val,
            health_score=health_val,
            time_score=time_val,
            snapshot_reason="Manual Recalculation",
            timestamp=datetime.utcnow(),
            confidence=1.0
        )
        db.add(viv_index)
        db.commit()
        
        return {
            "status": "success", 
            "message": "Scores recalculation complete",
            "scores": {
                "financial": fin_val,
                "health": health_val,
                "time": time_val
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        try:
            db.rollback()
        except Exception:
            pass
        return {"status": "error", "message": f"Calculation failed: {str(e)}"}

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


