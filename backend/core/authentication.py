"""
Auth0-only authentication utilities for production.

This module handles Auth0 JWT token validation and user management.
All authentication is delegated to Auth0 for maximum security.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from models.database import get_db
from models.models import User as DBUser
from pydantic import BaseModel
import core.config
from loguru import logger
import uuid

# OAuth2 scheme for FastAPI. Clients will send tokens in Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from typing import Dict, Any

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Bcrypt verification error: {e}")
        return False

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def get_user(db: Session, username: str) -> Optional[DBUser]:
    return db.query(DBUser).filter(DBUser.email == username).first()

def authenticate_user(db: Session, username: str, password: str) -> Optional[DBUser]:
    user = get_user(db, username)
    if not user or not user.hashed_password:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def create_access_token(data: Dict[str, Any], expires_minutes: Optional[float] = None) -> str:
    settings = core.config.get_settings()
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALG)
    return encoded_jwt


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserSchema(BaseModel):
    """Pydantic model for User data."""
    id: str
    username: str
    disabled: Optional[bool] = None


async def get_current_user(request: Request, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> DBUser:
    """
    Validate Auth0 JWT token and return corresponding user from database.
    Auto-creates user on first Auth0 login if they don't exist.
    
    Args:
        request: FastAPI Request object.
        token: Bearer token from Authorization header or cookie.
        db: Database session.
        
    Returns:
        DBUser: The authenticated user instance.
        
    Raises:
        HTTPException(401): If token is missing, invalid, or user creation fails.
    """
    settings = core.config.get_settings()
    
    # DEV BYPASS: Allow X-Test-User-Id header for testing when not in prod
    if settings.ENV != "prod":
        test_user_id = request.headers.get("X-Test-User-Id")
        if test_user_id:
            # Try by ID first, then by email
            user = db.query(DBUser).filter(DBUser.id == test_user_id).first()
            if not user:
                user = db.query(DBUser).filter(DBUser.email == test_user_id).first()
            if user:
                return user

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Try to get token from cookie if header token is missing
    active_token = token
    logger.debug(f"Auth - Header Token: {token[:10] if token else 'None'}...")
    
    if not active_token:
        cookie_token = request.cookies.get("access_token")
        logger.debug(f"Auth - Cookie Token found: {bool(cookie_token)}")
        if cookie_token:
            if cookie_token.startswith("Bearer "):
                active_token = cookie_token[7:]
            else:
                active_token = cookie_token
                
    if not active_token:
        logger.warning("Auth failed - No token found in header or cookie.")
        logger.debug(f"Auth - All cookies: {list(request.cookies.keys())}")
        raise credentials_exception

    # Validate Auth0 JWT token
    try:
        # Some clients might send the literal string "undefined" or "null"
        if active_token in ["undefined", "null", ""]:
             logger.warning(f"Auth failed - Token is literal '{active_token}'")
             raise credentials_exception
              
        from core.auth0_utils import verify_auth0_jwt
        payload = verify_auth0_jwt(active_token)
        
        # Extract Auth0 user information
        auth0_id = payload.get("sub")  # Auth0 user ID (e.g. google-oauth2|12345)
        email = payload.get("email")
        name = payload.get("name", email.split("@")[0] if email else "User")
        
        # Find or create user in database
        # First try finding by auth0_id
        user = db.query(DBUser).filter(DBUser.auth0_id == auth0_id).first()
        
        if not user and email:
             # Fallback to email for existing users
             user = db.query(DBUser).filter(DBUser.email == email).first()
             if user and not user.auth0_id:
                 # Link existing user to Auth0
                 user.auth0_id = auth0_id
                 db.commit()
                 logger.info(f"Linked existing user {email} to Auth0 ID {auth0_id}")
             
        if user:
            logger.info(f"Auth0 user authenticated: {email}")
            return user
        else:
            # Auto-create user on first Auth0 login
            logger.info(f"Creating new user from Auth0: {email}")
            new_user = DBUser(
                id=str(uuid.uuid4()),
                email=email,
                auth0_id=auth0_id,
                profile_json={"name": name},
                hashed_password=None,  # Auth0 users don't have local passwords
                account_status="ACTIVE",
                role="user"
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            logger.info(f"Auto-created Auth0 user: {email}")
            return new_user
            
    except Exception as e:
        logger.error(f"Auth0 token validation failed: {e}")
        raise credentials_exception


__all__ = ["Token", "UserSchema", "get_current_user", "oauth2_scheme", "get_password_hash", "verify_password", "authenticate_user", "create_access_token"]
