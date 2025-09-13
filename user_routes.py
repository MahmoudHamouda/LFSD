"""
User authentication and profile endpoints.

This router exposes endpoints for obtaining JWT access tokens and retrieving the
current user's profile. Authentication is handled via ``authentication.py``.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status

from authentication import (
    authenticate_user,
    create_access_token,
    get_current_user,
)
from rate_limiting import limiter


router = APIRouter(prefix="/user", tags=["User"])


@router.post("/token", summary="Obtain an access token")
@limiter.limit("20/minute")
async def login_for_access_token(request: Request) -> dict[str, str]:
    """
    Validate user credentials and return a JWT access token. This endpoint accepts
    credentials either as a JSON object (``{"username": "", "password": ""}``) or
    as URL‑encoded form data. It avoids using ``Form`` from FastAPI to
    eliminate the dependency on ``python-multipart``, which may not be
    installed in some environments.
    """
    # Try to parse JSON body first
    username = None
    password = None
    try:
        data = await request.json()
        if isinstance(data, dict):
            username = data.get("username")
            password = data.get("password")
    except Exception:
        # Not JSON; ignore and parse as urlencoded
        pass
    if username is None or password is None:
        # Fallback: parse urlencoded body manually
        body_bytes = await request.body()
        try:
            from urllib.parse import parse_qs

            parsed = parse_qs(body_bytes.decode())
            username = parsed.get("username", [None])[0]
            password = parsed.get("password", [None])[0]
        except Exception:
            username = None
            password = None
    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password must be provided",
        )
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