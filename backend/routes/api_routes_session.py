
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from typing import Optional
from pydantic import BaseModel

from models.database import get_db
from models.models import User
from core.authentication import (
    authenticate_user,
    create_access_token,
    get_current_user
)
import core.config
import logging

logger = logging.getLogger(__name__)

# Define schemas
class SessionLoginRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: str

class OnboardingProgressRequest(BaseModel):
    step: str
    data: Optional[dict] = None

class SessionResponse(BaseModel):
    authenticated: bool
    user: Optional[dict] = None
    message: Optional[str] = None

router = APIRouter(prefix="/auth", tags=["Session"])

@router.get("/session", response_model=SessionResponse)
async def check_session(
    response: Response,
    current_user: User = Depends(get_current_user), # This relies on Authorization header usually
    db: Session = Depends(get_db)
):
    """
    Returns the current session state.
    Used by frontend to determine authStatus and onboarding redirection.
    """
    # Ensure we return the freshest data
    db.refresh(current_user)
    logger.debug(f"DEBUG: /session checking user {current_user.id}. Status from DB: {current_user.onboarding_status}")
    
    return SessionResponse(
        authenticated=True,
        user={
            "id": current_user.id,
            "email": current_user.email,
            "name": current_user.profile_json.get("name") if current_user.profile_json else "",
            "onboarding_status": current_user.onboarding_status,
            "onboarding_step": current_user.onboarding_step,
            "onboarding_version": current_user.onboarding_version
        }
    )

@router.post("/login")
@router.post("/login_testing")
async def login(
    payload: SessionLoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    identifier = payload.email if payload.email else payload.username
    if not identifier:
         raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username required"
        )
    
    user = authenticate_user(db, identifier, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Create tokens
    access_token_expires = timedelta(minutes=60 * 24) # 1 day for dev
    access_token = create_access_token(
        data={"sub": user.email}, expires_minutes=access_token_expires.total_seconds() / 60
    )
    
    # Set HttpOnly cookie (basic implementation)
    response.set_cookie(
        key=core.config.get_settings().SESSION_COOKIE_NAME,
        value=f"Bearer {access_token}",
        httponly=True,
        secure=core.config.get_settings().ENV == "production", # Dev mode, set True in prod
        samesite="lax"
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "onboarding_status": user.onboarding_status,
            "onboarding_step": user.onboarding_step
        }
    }

@router.post("/logout")
async def logout(response: Response):
    """
    Logout the user by clearing authentication cookies.
    """
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="oauth_state")
    response.delete_cookie(key="token") # Fallback
    return {"message": "Logged out successfully"}

# User-specific onboarding routes
# Note: Changing prefix manually or using a separate router for /users/{id}/...
# Detailed requirement: POST /users/:id/onboarding/progress

user_router = APIRouter(prefix="/users", tags=["Onboarding"])

from fastapi import Body
from models.growth_models import Subscription
from models.growth_schemas import PlanId

class OnboardingCompleteRequest(BaseModel):
    plan_id: Optional[str] = None

# ... existing code ...

@user_router.post("/{user_id}/onboarding/progress")
async def update_onboarding_progress(
    user_id: str,
    payload: OnboardingProgressRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    current_user.onboarding_status = "IN_PROGRESS"
    current_user.onboarding_step = payload.step
    current_user.updated_at = datetime.utcnow()
    
    db.commit()
    return {"status": "success", "step": payload.step}

@user_router.post("/{user_id}/onboarding/complete")
async def complete_onboarding(
    user_id: str,
    payload: OnboardingCompleteRequest = Body(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Re-query user to ensure attached to current session and avoid detachment issues
    user_to_update = db.query(User).filter(User.id == current_user.id).first()
    logger.debug(f"DEBUG: /complete called for user {current_user.id}. Current status: {user_to_update.onboarding_status if user_to_update else 'NOT FOUND'}")
    
    if user_to_update:
        user_to_update.onboarding_status = "COMPLETE"
        user_to_update.onboarding_step = None
        user_to_update.updated_at = datetime.utcnow() # Force update with correct type
        
        # Handle Plan Selection
        if payload and payload.plan_id:
             logger.info(f"Processing plan selection: {payload.plan_id}")
             # Validate plan_id (simple check)
             if payload.plan_id in [PlanId.FREE, PlanId.PLUS, PlanId.PRO]:
                 # Find existing sub
                 sub = db.query(Subscription).filter(Subscription.user_id == user_id).first()
                 if sub:
                     if sub.plan_id != payload.plan_id:
                         logger.info(f"Upgrading user {user_id} from {sub.plan_id} to {payload.plan_id}")
                         sub.plan_id = payload.plan_id
                         sub.updated_at = datetime.utcnow()
                 else:
                     # Create if missing (failsafe)
                     logger.info(f"Creating new subscription for {user_id}: {payload.plan_id}")
                     new_sub = Subscription(user_id=user_id, plan_id=payload.plan_id, status="active")
                     db.add(new_sub)
        
        db.commit()
        db.refresh(user_to_update)
        logger.debug(f"DEBUG: /complete committed. New status: {user_to_update.onboarding_status}")
    
    return {"status": "success", "message": "Onboarding complete"}

