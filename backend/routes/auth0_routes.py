"""
Auth0-based Authentication Routes
Replaces custom password authentication with Auth0
"""
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from models.database import get_db
from models import User
from core.auth0_utils import verify_auth0_token
from core.auth0_config import get_auth0_settings
import uuid
from datetime import datetime
from typing import Optional

router = APIRouter(prefix="/auth", tags=["auth"])


class Auth0CallbackPayload(BaseModel):
    """Payload from frontend after Auth0 authentication"""
    token: str  # Auth0 access token


class UserResponse(BaseModel):
    """User data response"""
    id: str
    email: str
    name: str
    onboarding_status: str
    auth0_id: str


@router.get("/config")
async def get_auth0_config():
    """
    Return Auth0 configuration for frontend
    This is safe to expose as it only contains public info
    """
    settings = get_auth0_settings()
    return {
        "domain": settings.AUTH0_DOMAIN,
        "clientId": settings.AUTH0_CLIENT_ID,
        "audience": settings.AUTH0_AUDIENCE
    }


@router.post("/callback", response_model=UserResponse)
async def auth0_callback(
    payload: Auth0CallbackPayload, 
    db: Session = Depends(get_db)
):
    """
    Handle Auth0 callback after successful authentication
    Creates or updates user in database
    """
    try:
        # Verify the Auth0 token (this will raise HTTPException if invalid)
        from fastapi.security import HTTPAuthorizationCredentials
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=payload.token
        )
        token_payload = verify_auth0_token(credentials)
        
        # Access Token might not have email/name claims.
        # Fetch user info from Auth0 /userinfo endpoint
        import requests
        from core.auth0_config import get_auth0_settings
        settings = get_auth0_settings()
        
        userinfo_url = f"https://{settings.AUTH0_DOMAIN}/userinfo"
        userinfo_resp = requests.get(userinfo_url, headers={"Authorization": f"Bearer {payload.token}"})
        
        if not userinfo_resp.ok:
             print(f"Failed to fetch userinfo: {userinfo_resp.text}")
             # Fallback to token claims if userinfo fails (unlikely)
             user_info = token_payload
        else:
             user_info = userinfo_resp.json()

        # Extract user info
        auth0_id = user_info.get("sub")  # Auth0 user ID
        email = user_info.get("email")
        if not email:
            # Fallback if email missing in userinfo
            email = token_payload.get("email")
            
        name = user_info.get("name")
        if not name:
            name = email.split("@")[0] if email else "User"
        
        if not auth0_id or not email:
            raise HTTPException(
                status_code=400,
                detail="Invalid token: missing user information"
            )
        
        # Check if user exists by auth0_id
        user = db.query(User).filter(User.auth0_id == auth0_id).first()
        
        if not user:
            # Check if user exists by email (for migration)
            user = db.query(User).filter(User.email == email).first()
            
            if user:
                # Link existing user to Auth0 ID
                user.auth0_id = auth0_id
                if user.email == "finance@helm.com":
                    user.onboarding_status = "COMPLETE"
                user.updated_at = datetime.utcnow()
            else:
                # Create new user
                user = User(
                    id=str(uuid.uuid4()),
                    email=email,
                    auth0_id=auth0_id,
                    profile_json={"name": name},
                    onboarding_status="COMPLETE" if email == "finance@helm.com" else "NOT_STARTED",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(user)
        
        db.commit()
        db.refresh(user)
        
        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.profile_json.get("name", "") if user.profile_json else name,
            onboarding_status=user.onboarding_status or "NOT_STARTED",
            auth0_id=user.auth0_id
        )
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        import traceback
        print(f"[AUTH0 CALLBACK ERROR] {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Authentication callback failed: {str(e)}"
        )


@router.get("/me")
async def get_current_user(
    token_payload: dict = Depends(verify_auth0_token),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user
    Protected route - requires valid Auth0 token
    """
    try:
        auth0_id = token_payload.get("sub")
        
        user = db.query(User).filter(User.auth0_id == auth0_id).first()
        
        if not user:
            # Auto-create if missing (JIT provisioning for robustness)
            # Fetch user email from token if possible
            # But normally we return 404. Let's return 404 to be safe.
            raise HTTPException(
                status_code=404,
                detail="User not found. Please complete signup."
            )
        
        # Universal JIT Auto-Seeding
        # If user has no financial accounts, seed them with sample data (demo mode)
        # This ensures every new signup immediately sees the "Happy Path"
        from core.seeding import seed_user_data
        # seed_user_data internally checks if data exists before writing
        seeded = seed_user_data(db, user.id, "finance")
        if seeded:
             print(f"Universal seeding applied for {user.email}")
             db.commit()
                 
        user_data = {
            "id": user.id,
            "email": user.email,
            "name": user.profile_json.get("name", "") if user.profile_json else "",
            "onboarding_status": "COMPLETE", # Force complete for everyone in demo
            "auth0_id": user.auth0_id
        }

        # Return wrapped response to match frontend expectation
        return {
            "status": "ok",
            "user": user_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[GET USER ERROR] {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch user: {str(e)}"
        )


@router.post("/logout")
async def logout():
    """
    Logout endpoint (frontend handles Auth0 logout)
    This endpoint exists for API consistency
    """
    return {"message": "Logout successful"}
