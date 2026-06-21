"""
Time Utils Helper Module
"""

import dateparser
import datetime
import pytz
from typing import Optional, Dict, Any, Union
from loguru import logger


def parse_datetime(
    time_str: str,
    timezone: str = "UTC",
    languages: Optional[list] = None,
    future: bool = True,
) -> Optional[datetime.datetime]:
    """
    Robustly parses a natural language time string into a timezone-aware datetime object (UTC).

    Args:
        time_str: The natural language time string (e.g., "tomorrow at 3pm").
        timezone: The user's timezone string (e.g. "Asia/Dubai"). Defaults to UTC.
        languages: List of language codes to guide parsing (e.g., ['en', 'ar']).
        future: If True, ambiguous dates are parsed as future dates.

    Returns:
        TimeZone-aware datetime object (normalized to UTC) if successful, None otherwise.

    Usage:
        dt = parse_datetime("tomorrow 3pm", timezone="Asia/Dubai")
    """
    if not time_str or not isinstance(time_str, str):
        return None

    try:
        settings = {
            "PREFER_DATES_FROM": "future" if future else "current_period",
            "TIMEZONE": timezone,
            "RETURN_AS_TIMEZONE_AWARE": True,
            "TO_TIMEZONE": "UTC",  # Normalize output to UTC
        }

        # Default language support
        if not languages:
            languages = ["en", "ar"]  # Support English and Arabic by default

        dt = dateparser.parse(time_str, settings=settings, languages=languages)

        if not dt:
            logger.warning(f"Failed to parse time string: '{time_str}'")
            return None

        # Validation Bounds
        now = datetime.datetime.now(datetime.timezone.utc)

        # Prevent far past dates if we expect future (ignoring small clock skew/ "just now")
        if future and dt < (now - datetime.timedelta(hours=1)):
            logger.warning(f"Parsed date is in the past: {dt} (Input: {time_str})")
            # We assume if they said "yesterday" they meant it, but if we strictly wanted future:
            # return None
            # pass # Allow past dates for flexibility

        # Max horizon (e.g., 5 years) to prevent typos like "in 200 years"
        if dt > (now + datetime.timedelta(days=365 * 5)):
            logger.warning(
                f"Parsed date is too far in future: {dt} (Input: {time_str})"
            )
            return None

        return dt

    except Exception as e:
        logger.error(f"Error parsing time string '{time_str}': {e}")
        return None


def parse_time_slot(time_str: str) -> Optional[datetime.datetime]:
    """
    Deprecated Wrapper for backward compatibility.
    Use parse_datetime instead.
    """
    return parse_datetime(time_str)
