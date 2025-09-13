"""
Simple JWT authentication utilities.

This module provides functions for hashing passwords, verifying user credentials
and generating JSON Web Tokens (JWT). It uses a minimalist in‑memory user
store for demonstration purposes. For production use, replace the fake user
database with a persistent store (e.g. SQLAlchemy) and implement proper
credential validation.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
import jwt

from pydantic import BaseModel

from config import get_settings

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for FastAPI. Clients will send tokens in Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/user/token")


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class User(BaseModel):
    username: str
    disabled: Optional[bool] = None


class UserInDB(User):
    hashed_password: str


# Fake user database for demonstration. Replace with persistent store.
_fake_users_db: Dict[str, Dict[str, Any]] = {
    "alice": {
        "username": "alice",
        "hashed_password": pwd_context.hash("password"),
        "disabled": False,
    }
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plain text password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a plain text password."""
    return pwd_context.hash(password)


def get_user(username: str) -> Optional[UserInDB]:
    """Return a user from the in‑memory DB if present."""
    user = _fake_users_db.get(username)
    if not user:
        return None
    return UserInDB(**user)


def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Validate a user's credentials and return the user if correct."""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: Dict[str, Any], expires_minutes: Optional[int] = None) -> str:
    """Create a signed JWT token with an optional expiry."""
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALG)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Decode a JWT and return the corresponding user."""
    settings = get_settings()
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALG])
        username: str = payload.get("sub")  # subject claim
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    user = get_user(username)
    if user is None:
        raise credentials_exception
    return user