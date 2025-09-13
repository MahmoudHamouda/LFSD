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
# Attempt to import optional dependencies. We fallback to simple implementations
try:
    from passlib.context import CryptContext  # type: ignore
except Exception:
    CryptContext = None  # type: ignore

try:
    import jwt  # type: ignore
except Exception:
    jwt = None  # type: ignore

from pydantic import BaseModel

from config import get_settings

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
        # Store hashed passwords using pwd_context. The dummy context stores plain text.
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
    """
    Create a signed JWT token with an optional expiry. If PyJWT is unavailable,
    fall back to returning a simple bearer token derived from the user identity.

    The returned token will include the standard ``exp`` claim when using PyJWT.
    In fallback mode, the token is simply the username (``sub`` claim) and no
    expiry is encoded.
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
    # to_encode may contain ``sub`` or other keys. We'll prefer ``sub``.
    return str(to_encode.get("sub") or to_encode.get("username") or "token")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Decode a JWT and return the corresponding user. If PyJWT is unavailable,
    treat the bearer token as the username directly. Raises HTTP 401 if the
    token is invalid or the user does not exist.
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
        except Exception:
            raise credentials_exception
    else:
        # In fallback mode, the token itself is the username
        username = token
    if not username:
        raise credentials_exception
    user = get_user(username)
    if user is None:
        raise credentials_exception
    return user