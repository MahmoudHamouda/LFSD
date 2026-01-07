"""
Simple test router to verify basic functionality
No database access - just returns static JSON
"""
from fastapi import APIRouter

router = APIRouter(prefix="/test", tags=["test"])


@router.get("/ping")
async def ping():
    """
    Simple ping endpoint - no database, no Auth0, nothing
    If this works, the backend is starting correctly
    """
    return {"status": "ok", "message": "Backend is alive!"}


@router.get("/env")
async def check_env():
    """
    Check environment configuration
    """
    import os
    return {
        "debug": os.getenv("DEBUG", "not set"),
        "has_gemini_key": "set" if os.getenv("GEMINI_API_KEY") else "not set"
    }
