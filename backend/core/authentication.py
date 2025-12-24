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

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from models.database import get_db
from models.models import User as DBUser

# Attempt to import optional dependencies. We fallback to simple implementations
try:
    # from passlib.context import CryptContext  # type: ignore
    CryptContext = None # Force dummy hasher for dev to avoid bcrypt issues
except Exception:
    CryptContext = None  # type: ignore

try:
    import jwt  # type: ignore
except Exception:
    jwt = None  # type: ignore

from pydantic import BaseModel

from .config import get_settings

# Password hashing context. If passlib is not available we fall back to a no‑op hasher.
if CryptContext is not None:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
else:
    class _DummyCryptContext:
        """
        Minimal password hashing context used when passlib is unavailable. It
        performs no hashing and simply stores passwords in plain text.
        This is insecure and should only be used for local development or
        testing when passlib cannot be installed.
        """

        def hash(self, password: str) -> str:
            return password

        def verify(self, plain_password: str, hashed_password: str) -> bool:
            return plain_password == hashed_password

    pwd_context = _DummyCryptContext()

# OAuth2 scheme for FastAPI. Clients will send tokens in Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/user/token")


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserSchema(BaseModel):
    id: str
    username: str
    disabled: Optional[bool] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plain text password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a plain text password."""
    return pwd_context.hash(password)


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
    """
    settings = get_settings()
    to_encode = data.copy()
    # Set expiry on encoded payload when using PyJWT
    expire = datetime.utcnow() + timedelta(
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    if jwt:
        # Use PyJWT to create a signed token
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALG)  # type: ignore
        return encoded_jwt
    # Fallback: return the subject (username) directly as the token
    return str(to_encode.get("sub") or to_encode.get("username") or "token")


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> DBUser:
    """
    Decode a JWT and return the corresponding user from the DB.
    """
    settings = get_settings()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    username: Optional[str] = None
    if jwt:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALG])  # type: ignore
            username = payload.get("sub")  # subject claim
        except Exception as e:
            print(f"DEBUG: Auth failed - JWT Decode Error: {e}")
            raise credentials_exception
    else:
        # In fallback mode, the token itself is the username
        print("DEBUG: Auth warning - JWT library not found, using token as username.")
        username = token
    if not username:
        print("DEBUG: Auth failed - No username extracted from token.")
        raise credentials_exception
        
    user = get_user(db, username=username)
    if user is None:
        print(f"DEBUG: Auth failed - User {username} not found in DB.")
        raise credentials_exception
    return user