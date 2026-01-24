"""
Simple JWT authentication utilities.

This module provides functions for hashing passwords, verifying user credentials
and generating JSON Web Tokens (JWT). It uses a minimalist in-memory user
store for demonstration purposes. For production use, replace the fake user
database with a persistent store (e.g. SQLAlchemy) and implement proper
credential validation.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from models.database import get_db
from models.models import User as DBUser
from pydantic import BaseModel
from .config import get_settings

from passlib.context import CryptContext
from loguru import logger
import jwt
import bcrypt

# Password hashing context.
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") # Deprecated due to bcrypt 4.0 incompatibility

# OAuth2 scheme for FastAPI. Clients will send tokens in Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/user/token", auto_error=False)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserSchema(BaseModel):
    """Pydantic model for User data."""
    id: str
    username: str
    disabled: Optional[bool] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plain text password against a hashed password."""
    # return pwd_context.verify(plain_password, hashed_password)
    if not hashed_password:
        return False
    try:
        # Handle cases where hash might be plain string "SOCIAL_LOGIN..."
        if not hashed_password.startswith("$2"):
            return False
            
        params = plain_password.encode('utf-8')
        p_hash = hashed_password.encode('utf-8')
        return bcrypt.checkpw(params, p_hash)
    except Exception as e:
        print(f"Bcrypt verification error: {e}")
        return False


def get_password_hash(password: str) -> str:
    """Hash a plain text password."""
    # return pwd_context.hash(password)
    # Ensure password is truncated to 72 bytes if needed? No, user should know.
    # But usually we don't assume long passwords.
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def get_user(db: Session, username: str) -> Optional[DBUser]:
    """Return a user from the DB if present."""
    # In our model, email is the username
    user = db.query(DBUser).filter(DBUser.email == username).first()
    if not user:
        print(f"DEBUG: User {username} not found in DB.")
        try:
            all_users = db.query(DBUser).all()
            print(f"DEBUG: All users in DB: {[u.email for u in all_users]}")
            with open("auth_debug.log", "a") as f:
                f.write(f"User {username} not found. All users: {[u.email for u in all_users]}\n")
        except Exception as e:
            print(f"DEBUG: Error listing users: {e}")
    return user


def authenticate_user(db: Session, username: str, password: str) -> Optional[DBUser]:
    """Validate a user's credentials and return the user if correct."""
    user = get_user(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: Dict[str, Any], expires_minutes: Optional[int] = None) -> str:
    """
    Create a signed JWT token with an optional expiry.
    
    Args:
        data: The payload to encode (e.g., {"sub": "user@example.com"}).
        expires_minutes: Optional override for token lifespan.
        
    Returns:
        Encoded JWT string.
    """
    settings = get_settings()
    to_encode = data.copy()
    # Set expiry on encoded payload when using PyJWT
    expire = datetime.utcnow() + timedelta(
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    to_encode.update({"exp": expire})
    # Use PyJWT to create a signed token
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALG)
    return encoded_jwt


async def get_current_user(request: Request, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> DBUser:
    """
    Decode a JWT and return the corresponding user from the DB.
    Supports both Authorization header (Bearer token) and HttpOnly cookie (access_token).
    
    Args:
        request: FastAPI Request object.
        token: Bearer token from Authorization header.
        db: Database session.
        
    Returns:
        DBUser: The authenticated user instance.
        
    Raises:
        HTTPException(401): If token is missing, invalid, or user not found.
    """
    settings = get_settings()
    
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
            # Create user if bypass used but not found? No, just try to find.

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Try to get token from cookie if header token is missing or generic/empty
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
        # log all cookies for debugging
        logger.debug(f"Auth - All cookies: {list(request.cookies.keys())}")
        raise credentials_exception

    username: Optional[str] = None
    # 1. Try Legacy HS256 Decode (Native Tokens)
    try:
        # Some clients might send the literal string "undefined" or "null" if JS is messy
        if active_token in ["undefined", "null", ""]:
             logger.warning(f"Auth failed - Token is literal '{active_token}'")
             raise credentials_exception
             
        payload = jwt.decode(active_token, settings.SECRET_KEY, algorithms=[settings.JWT_ALG])
        username = payload.get("sub")  # subject claim
        logger.info(f"Auth - Decoded (Legacy) username: {username}")
    except Exception as legacy_e:
        # 2. Try Auth0 RS256 Decode (Social/Auth0 Tokens)
        try:
            from core.auth0_utils import verify_auth0_jwt
            payload = verify_auth0_jwt(active_token)
            # Auth0 'sub' is the Auth0 ID (e.g. google-oauth2|12345)
            # We also might get email
            auth0_id = payload.get("sub")
            email = payload.get("email")
            
            # We need to resolve this to a DB User
            # First try finding by auth0_id
            user = db.query(DBUser).filter(DBUser.auth0_id == auth0_id).first()
            if not user and email:
                 # Fallback to email
                 user = db.query(DBUser).filter(DBUser.email == email).first()
                 
            if user:
                return user
            else:
                logger.warning(f"Auth0 Token Valid but User not found in DB. Sub: {auth0_id}")
                raise credentials_exception
                
        except Exception as auth0_e:
            logger.error(f"Auth failed - Legacy: {legacy_e} | Auth0: {auth0_e}")
            raise credentials_exception
        
    if not username:
        logger.warning("Auth failed - No username extracted from token.")
        raise credentials_exception
        
    user = get_user(db, username=username)
    if user is None:
        logger.warning(f"Auth failed - User {username} not found in DB.")
        raise credentials_exception
    return user
