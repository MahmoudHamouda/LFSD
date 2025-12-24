# Utility helpers for the Gemini service

"""Functions that help the Gemini service discover the best model to use.

The function `get_latest_gemini_model` queries the Gemini API for the list of
available generative models and returns the most recent one (by lexical order).
If the API call fails, it falls back to a known stable model name.
"""

import logging
from typing import List
import google.generativeai as genai

log = logging.getLogger("gemini_utils")


def get_latest_gemini_model() -> str:
    """Return the name of the newest Gemini model supported by the current API.

    The Gemini API provides a `list_models` method.  We filter for models that
    support `generateContent`, sort them, and pick the last entry.  If anything
    goes wrong we log the error and return a safe fallback (`gemini-1.5-flash`).
    """
    try:
        models = genai.list_models()
        # Keep only generative models (those that can generate content)
        generative_names: List[str] = [
            m.name for m in models if "generateContent" in getattr(m, "supported_generation_methods", [])
        ]
        if not generative_names:
            raise RuntimeError("No generative models returned from Gemini API")
        latest = sorted(generative_names)[-1]
        log.info("Auto‑selected latest Gemini model: %s", latest)
        return latest
    except Exception as exc:  # pragma: no cover – defensive fallback
        log.error("Failed to list Gemini models: %s", exc)
        # Fallback to a model that is widely available
        return "gemini-1.5-flash"

