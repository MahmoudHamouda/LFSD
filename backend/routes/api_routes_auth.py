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
    state: str



# Retrying with correct imports handling
from fastapi import Response, Request

@router.get("/google/url")
async def google_auth_url(response: Response, db: Session = Depends(get_db)):
    from services.google_calendar_service import GoogleCalendarService
    
    # Generate random state for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Use a dummy user_id since we are just getting the URL
    service = GoogleCalendarService(db, user_id="auth_init")
    
    url = service.get_auth_url(state=state)
    
    # Set state in HTTPOnly cookie to verify on callback
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        samesite="lax",
        secure=True, # Should be True in Prod, ensure SSL is used
        max_age=600  # 10 minutes
    )
    
    return {"url": url}

@router.post("/google/callback")
async def google_auth_callback(payload: CodePayload, request: Request, db: Session = Depends(get_db)):
    # Verify state
    cookie_state = request.cookies.get("oauth_state")
    if not cookie_state or not payload.state or cookie_state != payload.state:
        print(f"[AUTH] CSRF State Mismatch. Cookie: {cookie_state}, Payload: {payload.state}")
        raise HTTPException(status_code=400, detail="Invalid state parameter. Possible CSRF attempt.")

    from services.google_calendar_service import GoogleCalendarService
    from models.models import Connection # Ensure Connection is imported
    
    # We use a placeholder user_id initially because we don't know the user yet
    # Ideally, we should just use the service's static methods or helpers, 
    # but the service is designed around an instance with user_id. 
    # We will instantiate it with specific "auth_callback" ID just to get the exchange method.
    service = GoogleCalendarService(db, user_id="auth_callback")
    
    try:
        # Exchange code for credentials
        # The service.exchange_code method expects a user_id to save the connection immediately.
        # However, we don't have the user_id until we get the email from the token.
        # We need to manually do what the service does but in the right order:
        # 1. Exchange code -> Get Tokens (without saving to a user yet)
        # 2. Get User Info -> Find/Create User
        # 3. Create/Update Connection for that User
        
        # Since service.exchange_code does ALL of this in one go for an *existing* user, 
        # it is not suitable for "Sign Up / Log In" flow where user is unknown.
        # We will manually call the token endpoint here or refactor the service.
        # For minimal intrusion, we replicate the "exchange" logic using requests directly or 
        # modify the service usage (but service insists on user_id).
        
        # Let's extract the exchange logic carefully.
        import requests
        token_payload = {
            "client_id": service.CLIENT_ID,
            "client_secret": service.CLIENT_SECRET,
            "code": payload.code,
            "grant_type": "authorization_code",
            "redirect_uri": service.REDIRECT_URI
        }
        
        token_resp = requests.post(service.TOKEN_URL, data=token_payload)
        if token_resp.status_code != 200:
             raise Exception(f"Failed to exchange code: {token_resp.text}")
        
        token_data = token_resp.json()
        
        # Get User Info
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        
        creds = Credentials(
            token=token_data.get("access_token"),
            refresh_token=token_data.get("refresh_token"),
            token_uri=service.TOKEN_URL,
            client_id=service.CLIENT_ID,
            client_secret=service.CLIENT_SECRET,
            scopes=token_data.get("scope", "").split(" ")
        )
        
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
                profile_json={"name": name}
            )
            db.add(user)
            db.commit() # Commit to get ID
            db.refresh(user)
            
        # Update Connection Record (Centralized Storage)
        connection = db.query(Connection).filter(
            Connection.user_id == user.id,
            Connection.provider == "google_calendar" # Or generic 'google'
        ).first()
        
        if not connection:
            connection = Connection(
                id=str(uuid.uuid4()),
                user_id=user.id,
                provider="google_calendar",
                status="connected"
            )
            db.add(connection)
            
        connection.access_token = token_data.get("access_token")
        connection.refresh_token = token_data.get("refresh_token")
        connection.token_type = token_data.get("token_type")
        connection.scope = token_data.get("scope")
        
        expires_in = token_data.get("expires_in", 3600)
        connection.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        connection.updated_at = datetime.utcnow()
        connection.status = "connected"

        # Clear potentially stale creds from profile if they exist (cleanup)
        if user.profile_json and "google_creds" in user.profile_json:
            p = user.profile_json.copy()
            del p["google_creds"]
            user.profile_json = p
            
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


