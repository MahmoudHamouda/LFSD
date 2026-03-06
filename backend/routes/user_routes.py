"""
User authentication and profile endpoints.

This router exposes endpoints for obtaining JWT access tokens and retrieving the
current user's profile. Authentication is handled via ``authentication.py``.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from models.database import get_db

from datetime import datetime
from core.authentication import (
    get_current_user,
)
from core.rate_limiting import limiter



router = APIRouter(prefix="/user", tags=["User"])


from models.models import FinancialAccount, FinancialTransaction, VivLog, User, OnboardingSession, VivIndex
# from core.authentication import get_password_hash # Removed for Auth0 migration
import uuid
from models.api_models import UserUpdateRequest
from services.financial_scoring import calculate_financial_health_score
from services.health_scoring import calculate_health_score
from services.time_scoring import calculate_productivity_score

@router.post("/register", summary="Register a new user")
async def register_user(
    user_data: dict,
    db: Session = Depends(get_db)
):
    """
    Register a new user. Optional onboarding_session_id to link financial data.
    """
    email = user_data.get("email")
    password = user_data.get("password")
    onboarding_session_id = user_data.get("onboarding_session_id")
    
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")
        
    # Check if user exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
        
    # Create user
    # Native registration disabled - using Auth0 for registration
    raise HTTPException(status_code=400, detail="Native registration is disabled. Please use Auth0.")
    
#    hashed_password = get_password_hash(password)
#    new_user = User(
#        email=email,
#        hashed_password=hashed_password,
#        profile_json=user_data.get("profile", {})
#    )
#    db.add(new_user)
#    db.commit()
#    db.refresh(new_user)
    
    # Handle onboarding session
    if onboarding_session_id:
        session = db.query(OnboardingSession).filter(OnboardingSession.id == onboarding_session_id).first()
        if session and session.data_json:
            # Extract metadata
            metadata = session.data_json.get("metadata", {})
            bank_name = metadata.get("bank_name", "Main Bank")
            account_type_raw = metadata.get("statement_type", "Checking").lower()
            
            # Map account type
            account_type = "checking"
            if "savings" in account_type_raw:
                account_type = "savings"
            elif "credit" in account_type_raw:
                account_type = "credit"
            elif "loan" in account_type_raw:
                account_type = "loan"

            # Create default account
            main_account = FinancialAccount(
                user_id=new_user.id,
                institution_name=bank_name,
                account_type=account_type,
                current_balance=0.0
            )
            db.add(main_account)
            db.commit()
            db.refresh(main_account)
            
            # Add transactions
            transactions_data = session.data_json.get("transactions", [])
            for t_data in transactions_data:
                # Basic mapping
                t_date = datetime.utcnow()
                if "date" in t_data:
                    try:
                        import dateparser
                        parsed_date = dateparser.parse(t_data["date"])
                        if parsed_date:
                            t_date = parsed_date
                    except ImportError:
                        pass # Fallback to now
                    except Exception:
                        pass

                transaction = FinancialTransaction(
                    account_id=main_account.id,
                    user_id=new_user.id,
                    amount=float(t_data.get("amount", 0)),
                    merchant_name=t_data.get("description", "Unknown"),
                    transaction_date=t_date
                )
                db.add(transaction)
            
            # Clean up session
            db.delete(session)
            db.commit()
            
    return {"message": "User registered successfully", "user_id": new_user.id}

@router.post("/token", summary="Obtain an access token")
@limiter.limit("20/minute")
async def login_for_access_token(
    request: Request,
    db: Session = Depends(get_db)
) -> dict[str, str]:
    """
    DEPRECATED: Use Auth0 endpoints instead.
    """
    raise HTTPException(status_code=410, detail="This endpoint is deprecated. Use Auth0 authentication.")

@router.get("/me", summary="Get current user profile")
@limiter.limit("60/minute")
async def read_users_me(request: Request, current_user=Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, Any]:
    """Return the profile of the authenticated user."""
    
    # Calculate Streaks
    user_id = current_user.id
    from models.models import HealthDailySummary
    summary_dates = db.query(HealthDailySummary.date).filter(
        HealthDailySummary.user_id == user_id
    ).order_by(HealthDailySummary.date.desc()).limit(30).all()
    
    check_in_streak = 0
    if summary_dates:
        import datetime as dt
        today = dt.date.today()
        dates = [d[0] for d in summary_dates]
        if today in dates or (today - dt.timedelta(days=1)) in dates:
            current = today
            if today not in dates:
                current = today - dt.timedelta(days=1)
            while current in dates:
                check_in_streak += 1
                current -= dt.timedelta(days=1)
        if today not in dates and check_in_streak == 0:
             yesterday = today - dt.timedelta(days=1)
             if yesterday in dates:
                 current = yesterday
                 check_in_streak = 1
                 while current in dates:
                     check_in_streak += 1
                     current -= dt.timedelta(days=1)
             else:
                 check_in_streak = 1
        elif today not in dates and check_in_streak > 0:
             check_in_streak += 1
    else:
        check_in_streak = 1
    
    index_count = db.query(VivIndex).filter(VivIndex.user_id == user_id).count()
    financial_streak = min(index_count, 52)

    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "username": current_user.email,
            "privacy": current_user.viv_preferences,
            "engagement": {
                "lastActive": datetime.utcnow().isoformat(),
                "streaks": {
                    "dailyCheckIn": check_in_streak,
                    "financialReview": financial_streak
                },
                "mostUsedJourneys": []
            },
            "identity": {
                "id": current_user.id,
                "email": current_user.email,
                "username": current_user.email,
                "firstName": current_user.profile_json.get("name", "").split(" ")[0] if current_user.profile_json else "",
                "lastName": current_user.profile_json.get("name", "").split(" ")[1] if current_user.profile_json and " " in current_user.profile_json.get("name", "") else "",
                "phoneNumber": current_user.profile_json.get("phone", "") if current_user.profile_json else "",
                "profile": current_user.profile_json,
                "vivPreferences": current_user.viv_preferences
            },
            "profile": current_user.profile_json
        }
    }

@router.patch("/me", summary="Update current user profile")
@limiter.limit("20/minute")
async def update_user_me(
    request: Request,
    updates: UserUpdateRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    """
    Update the authenticated user's profile, including identity, preferences,
    and onboarding data (triggers score recalculation).
    """

    # 1. Update Identity
    if updates.identity:
        ident = updates.identity
        if ident.firstName or ident.lastName:
            full_name = f"{ident.firstName or ''} {ident.lastName or ''}".strip()
            # Update name in profile_json
            profile = current_user.profile_json or {}
            profile = dict(profile)
            profile["name"] = full_name
            current_user.profile_json = profile

        if ident.phoneNumber:
             profile = current_user.profile_json or {}
             profile = dict(profile)
             profile["phone"] = ident.phoneNumber
             current_user.profile_json = profile

    # 2. Update Preferences
    if updates.vivPreferences:
        # Assuming viv_preferences is a JSON column
        current_prefs = current_user.viv_preferences or {}
        # Merge
        new_prefs = updates.vivPreferences.dict(exclude_unset=True)
        current_user.viv_preferences = {**current_prefs, **new_prefs}

    # 3. Update Onboarding Data & Recalculate Scores
    if updates.onboarding_data:
        payload = updates.onboarding_data
        
        # Ensure user_id in payload matches current user
        payload.user_id = current_user.id

        # Update profile_json with new onboarding data
        profile = current_user.profile_json or {}
        # Ensure new reference for SQLAlchemy detection
        profile = dict(profile)
        profile["onboarding_data"] = payload.dict()
        current_user.profile_json = profile

        # Recalculate Scores
        try:
            # Financial
            financial_data = calculate_financial_health_score(
                current_user.id, 
                payload.dict(), 
                db, 
                is_manual_mode=payload.is_manual_mode
            )
            
            # Health
            hs_data = calculate_health_score(current_user.id, payload.dict(), db)
            
            # Productivity
            tes_data = calculate_productivity_score(current_user.id, payload.dict(), db)

            # Save Viv Index
            viv_index = VivIndex(
                id=str(uuid.uuid4()),
                user_id=current_user.id,
                financial_score=financial_data["overall_score"],
                health_score=hs_data["score"],
                time_score=tes_data["score"],
                snapshot_reason="Profile Update",
                timestamp=datetime.utcnow()
            )
            db.add(viv_index)

            # Update breakdown in profile
            profile["onboarding_breakdown"] = {
                "financial": financial_data,
                "health": hs_data,
                "productivity": tes_data
            }
            current_user.profile_json = profile

        except Exception as e:
            print(f"Error recalculating scores during profile update: {e}")
            # Don't fail the whole request, but maybe add warning?
            pass

    db.commit()
    db.refresh(current_user)

    # Return updated structure matching User interface
    # Return updated structure matching User interface
    # Manual serialization to avoid Pydantic/SQLAlchemy conflicts
    
    viv_index_obj = db.query(VivIndex).filter(VivIndex.user_id == current_user.id).order_by(VivIndex.timestamp.desc()).first()
    viv_index_data = None
    if viv_index_obj:
        viv_index_data = {
            "financial_score": viv_index_obj.financial_score,
            "health_score": viv_index_obj.health_score,
            "time_score": viv_index_obj.time_score,
            "timestamp": viv_index_obj.timestamp
        }

    accounts = db.query(FinancialAccount).filter(FinancialAccount.user_id == current_user.id).all()
    accounts_data = [
        {
            "id": a.id,
            "institution_name": a.institution_name,
            "account_type": a.account_type,
            "current_balance": a.current_balance
        } for a in accounts
    ]

    transactions = db.query(FinancialTransaction).filter(FinancialTransaction.user_id == current_user.id).limit(5).all()
    recent_transactions_data = [
        {
            "id": t.id,
            "amount": t.amount,
            "merchant_name": t.merchant_name,
            "date": t.transaction_date,
            "category": t.category_primary
        } for t in transactions
    ]
    
    # Serialize Life Goals
    life_goals_data = [
        {
            "id": lg.id,
            "title": lg.title,
            "target_amount": lg.target_amount,
            "saved_amount": lg.saved_amount,
            "deadline": lg.deadline,
            "priority": lg.priority
        } for lg in current_user.life_goals
    ]

    # Serialize Connections
    connections_data = [
        {
            "id": c.id,
            "provider": c.provider,
            "status": c.status,
            "created_at": c.created_at
        } for c in current_user.connections
    ]

    ret_val = {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "username": current_user.email,
            "identity": {
                "id": current_user.id,
                "email": current_user.email,
                "username": current_user.email,
                "firstName": current_user.profile_json.get("name", "").split(" ")[0] if current_user.profile_json else "",
                "lastName": current_user.profile_json.get("name", "").split(" ")[1] if current_user.profile_json and " " in current_user.profile_json.get("name", "") else "",
                 "profile": current_user.profile_json,
                "vivPreferences": current_user.viv_preferences
            },
            "vivIndex": viv_index_data,
            "lifeGoals": life_goals_data,
            "accounts": accounts_data,
            "recentTransactions": recent_transactions_data,
            "healthConnections": connections_data,
            "profile": current_user.profile_json
        }
    }

    return ret_val

@router.get("/snapshot", summary="Get user snapshot")
@limiter.limit("60/minute")
async def get_user_snapshot(
    request: Request,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict[str, Any]:
    """
    Return a comprehensive snapshot of the user's state.
    """
    user_id = current_user.id
    
    # Use new models
    accounts = db.query(FinancialAccount).filter(FinancialAccount.user_id == user_id).all()
    transactions = db.query(FinancialTransaction).filter(FinancialTransaction.user_id == user_id).limit(10).all()
    logs = db.query(VivLog).filter(VivLog.user_id == user_id).order_by(VivLog.timestamp.desc()).limit(10).all()
    
    # Calculate totals
    total_balance = sum(acc.current_balance for acc in accounts if acc.account_type == 'checking')
    total_savings = sum(acc.current_balance for acc in accounts if acc.account_type == 'savings')
    total_debt = sum(acc.current_balance for acc in accounts if acc.account_type == 'credit')
    
    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "username": current_user.email,
            "profile": current_user.profile_json
        },
        "financials": {
            "income": 0, # Not directly stored in new schema, maybe derived
            "expenses": 0, # Derived
            "savings": total_savings,
            "debts": total_debt,
            "total_balance": total_balance
        },
        "transactions": [
            {
                "id": t.id, 
                "amount": t.amount, 
                "category": t.category_primary, 
                "date": t.transaction_date, 
                "description": t.merchant_name
            }
            for t in transactions
        ],
        "orders": [], # Deprecated
        "notifications": [], # Deprecated
        "activity_feed": [
            {
                "id": l.id, 
                "action": l.user_intent, 
                "details": l.decision_logic, 
                "timestamp": l.timestamp
            }
            for l in logs
        ]
    }
@router.post("/{user_id}/onboarding/complete", summary="Mark onboarding as complete")
async def complete_onboarding(
    user_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Finalize onboarding for the user.
    """
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this user")
        
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.onboarding_status = "COMPLETE"
    db.commit()
    
    return {"status": "success", "message": "Onboarding completed"}
