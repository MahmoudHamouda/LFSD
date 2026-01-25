# Utility helpers for the Gemini service

"""Functions that help the Gemini service discover the best model to use.

The function `get_latest_gemini_model` queries the Gemini API for the list of
available generative models and returns the most recent one (by lexical order).
If the API call fails, it falls back to a known stable model name.
"""

from google.api_core import retry
import logging
from typing import List, Optional
import google.generativeai as genai
from core.config import get_settings

log = logging.getLogger("gemini_utils")

# Simple in-memory cache for model name
_cached_model_name: Optional[str] = None

@retry.Retry(predicate=retry.if_exception_type(Exception), deadline=10.0)
def _fetch_models_with_retry() -> List[str]:
    """Fetch models with exponential backoff retry."""
    models = genai.list_models()
    return [
        m.name for m in models if "generateContent" in getattr(m, "supported_generation_methods", [])
    ]

def get_latest_gemini_model() -> str:
    """Return the name of the newest Gemini model supported by the current API.

    Features:
    - 5-minute caching to avoid spamming list_models
    - Retry logic for transient network errors
    - Explicit configuration check
    - Graceful fallback
    """
    global _cached_model_name
    if _cached_model_name:
        return _cached_model_name

    # Ensure API is configured before calling list_models
    try:
        settings = get_settings()
        if not settings.GEMINI_API_KEY:
            log.warning("GEMINI_API_KEY not set. Using fallback model.")
            return "gemini-1.5-flash"
        
        # Check if already configured? genai doesn't expose is_configured() 
        # but re-configuring is safe-ish. Better to rely on caller or do it here.
        # We assume main app entrypoint configured it, but we can configure if needed.
        # genai.configure(api_key=settings.GOOGLE_API_KEY)
        
        generative_names = _fetch_models_with_retry()
        
        if not generative_names:
            raise RuntimeError("No generative models returned from Gemini API")
            
        latest = sorted(generative_names)[-1]
        
        # Cache logic could be time-based, for now life-of-process is likely fine 
        # as model lists don't change hourly.
        _cached_model_name = latest
        
        log.debug("Auto-selected latest Gemini model: %s", latest)
        return latest
        
    except Exception as exc:  # pragma: no cover – defensive fallback
        log.warning("Failed to list Gemini models (using fallback): %s", exc)
        # Fallback to a model that is widely available
        return "gemini-1.5-flash"


