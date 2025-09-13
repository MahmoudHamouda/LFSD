"""
User authentication and profile endpoints.

This router exposes endpoints for obtaining JWT access tokens and retrieving the
current user's profile. Authentication is handled via ``authentication.py``.
"""

from typing import Any

from fastapi import APIRouter, Depends, Form, HTTPException, status

from authentication import (
    authenticate_user,
    create_access_token,
    get_current_user,
)
from rate_limiting import limiter


router = APIRouter(prefix="/user", tags=["User"])


@router.post("/token", summary="Obtain an access token")
@limiter.limit("20/minute")
async def login_for_access_token(
    *,
    username: str = Form(...),
    password: str = Form(...),
) -> dict[str, str]:
    """Validate user credentials and return a JWT access token."""
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token({"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", summary="Get current user profile")
@limiter.limit("60/minute")
async def read_users_me(*, current_user=Depends(get_current_user)) -> dict[str, Any]:
    """Return the profile of the authenticated user."""
    return {"data": current_user.dict()}