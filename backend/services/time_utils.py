"""
Time Utils Helper Module
"""
import dateparser
import datetime
from typing import Optional

def parse_time_slot(time_str: str) -> Optional[datetime.datetime]:
    """
    Parses a natural language time string into a datetime object.
    Prefers future dates.
    
    Args:
        time_str: The natural language time string (e.g., "tomorrow at 3pm").
        
    Returns:
        datetime object if successful, None otherwise.
    """
    if not time_str:
        return None
        
    settings = {'PREFER_DATES_FROM': 'future'}
    dt = dateparser.parse(time_str, settings=settings)
    return dt
