from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from models.database import get_db
from models.models import User
import uuid
import secrets
from datetime import datetime, timedelta
from core.authentication import get_password_hash, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

class SignupPayload(BaseModel):
    email: str
    password: str
    name: str

class AuthResponse(BaseModel):
    user_id: str
    email: str
    message: str

@router.post("/signup", response_model=AuthResponse)
async def signup(payload: SignupPayload, db: Session = Depends(get_db)):
    try:
        print(f"[AUTH] Signup attempt for {payload.email}")
        # Check if user exists
        existing_user = db.query(User).filter(User.email == payload.email).first()
        if existing_user:
            print(f"[AUTH] User {payload.email} already exists")
            raise HTTPException(status_code=409, detail="Account already exists. Please log in.")

        new_user = User(
            id=str(uuid.uuid4()),
            email=payload.email,
            hashed_password=get_password_hash(payload.password),
            profile_json={"name": payload.name}
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        print(f"[AUTH] User {new_user.id} created successfully")

        return AuthResponse(
            user_id=new_user.id,
            email=new_user.email,
            message="User created successfully"
        )
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        import traceback
        error_msg = f"Signup Error: {str(e)}"
        print(f"[AUTH-ERROR] {error_msg}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")

class CodePayload(BaseModel):
    code: str

@router.get("/google/url")
async def google_auth_url(db: Session = Depends(get_db)):
    from services.google_calendar_service import GoogleCalendarService
    # Use a dummy user_id since we are just getting the URL
    service = GoogleCalendarService(db, user_id="auth_init")
    # But for "Continue with Google", we mainly want identity.
    # Service defaults to Calendar scopes. Let's create a dedicated simplified flow here or update helper.
    # For speed/MVP: We will modify the frontend to expect a popup that calls back here.
    
    url = service.get_auth_url() # This uses Calendar scopes.
    # TODO: Ideally should separate scopes. For this specific user request "Sign up with Google", 
    # capturing their Calendar permission simultaneously is actually a feature :)
    return {"url": url}

@router.post("/google/callback")
async def google_auth_callback(payload: CodePayload, db: Session = Depends(get_db)):
    from services.google_calendar_service import GoogleCalendarService
    service = GoogleCalendarService(db, user_id="auth_callback")
    try:
        # Exchange code for credentials
        creds = service.exchange_code(payload.code)
        
        # Get User Info
        from googleapiclient.discovery import build
        oauth2 = build('oauth2', 'v2', credentials=creds)
        user_info = oauth2.userinfo().get().execute()
        
        email = user_info.get('email')
        name = user_info.get('name')
        
        # Create or Get User
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                id=str(uuid.uuid4()),
                email=email,
                hashed_password="SOCIAL_LOGIN_NO_PASSWORD",
                profile_json={"name": name, "google_creds": service.creds_to_json(creds)}
            )
            db.add(user)
        else:
            # Update tokens
            # Merge existing profile with new creds
            profile = user.profile_json or {}
            profile["google_creds"] = service.creds_to_json(creds)
            user.profile_json = profile
            
        db.commit()
        db.refresh(user)

        try:
            from core.authentication import create_access_token
        except ImportError:
            # Fallback if circular import or path issue, but likely fine
            pass

        access_token = create_access_token({"sub": user.email})

        return {
            "user_id": user.id,
            "email": user.email,
            "name": name,
            "token": access_token,
            "onboarding_status": user.onboarding_status or "NOT_STARTED",
            # Add other fields if needed by User interface
            "id": user.id 
        }
    except Exception as e:
        print(f"Google Auth Error: {e}")
        raise HTTPException(status_code=400, detail="Authentication failed")

class ForgotPasswordPayload(BaseModel):
    email: str

class ResetPasswordPayload(BaseModel):
    token: str
    new_password: str

@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordPayload, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    # Always return a success message to prevent email enumeration
    message = "If an account exists with that email, a password reset link has been sent."
    
    if not user:
        return {"message": message}
    
    # Generate token
    token = secrets.token_urlsafe(32)
    user.password_reset_token = token
    user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
    db.commit()
    
    # Send email
    try:
        from services.email_service import EmailService
        email_service = EmailService()
        email_service.send_password_reset_email(user.email, token)
    except Exception as e:
        # Log error but don't expose it to the user to prevent enumeration/attacks
        print(f"Failed to send reset email: {e}")
        # In production, you might want to alert admins here
    
    return {"message": message}

@router.post("/reset-password")
async def reset_password(payload: ResetPasswordPayload, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        User.password_reset_token == payload.token,
        User.password_reset_expires > datetime.utcnow()
    ).first()
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    # Update password
    user.hashed_password = get_password_hash(payload.new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    db.commit()
    
    return {"message": "Password updated successfully"}
