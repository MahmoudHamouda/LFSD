"""
Time Scoring Service
Calculates time management scores based on calendar events using the 5-Pillar Model.
"""
from datetime import datetime, timedelta
import pytz
from sqlalchemy.orm import Session
from sqlalchemy import func
from models.models import CalendarEvent, TimeScore
from typing import Dict, Optional, List, Tuple
from loguru import logger
import uuid

def calculate_time_score(db: Session, user_id: str, window_days: int = 30) -> Optional[TimeScore]:
    """
    Calculate comprehensive time score for a user based on calendar data.
    Uses the 5-Pillar Framework: Structure, Load, Focus, Friction, Stress.
    
    Args:
        db: Database session
        user_id: User ID
        window_days: Time window in days (default 30)
    
    Returns:
        Persisted TimeScore object with calculated subscores
    """
    logger.info(f"Calculating time score for user {user_id} over {window_days} days")
    
    # 1. Fetch Events (Standardized to UTC)
    now_utc = datetime.now(pytz.UTC)
    start_date = now_utc - timedelta(days=window_days)
    
    # Ensure start_date is naive if DB stores naive, or aware if aware. 
    # SQLAlchemy often handles this if the model is set up right, but we perform a safe check.
    # Assuming DB stores naive UTC (common pattern):
    start_date_naive = start_date.replace(tzinfo=None)

    events = db.query(CalendarEvent).filter(
        CalendarEvent.user_id == user_id,
        CalendarEvent.start_time >= start_date_naive
    ).all()
    
    if not events:
        logger.info(f"No calendar events found for user {user_id}")
        return None
    
    # 2. Preprocess & Normalize Events
    cleaned_events = _preprocess_events(events)
    if not cleaned_events:
        return None

    # 3. Calculate Pillars
    structure_metric = _calculate_structure(cleaned_events, window_days)
    load_metric = _calculate_load(cleaned_events, window_days)
    focus_metric = _calculate_focus(cleaned_events)
    friction_metric = _calculate_friction(cleaned_events)
    stress_metric = _calculate_stress(cleaned_events, window_days)
    
    # 4. Normalize Scores (0-100)
    # Each sub-function returns 0-100
    
    # 5. Weighted Overall Score
    # Structure (25%), Load (25%), Focus (20%), Friction (15%), Stress (15%)
    overall_score = (
        structure_metric * 0.25 +
        load_metric * 0.25 +
        focus_metric * 0.20 +
        friction_metric * 0.15 +
        stress_metric * 0.15
    )
    
    # 6. Snapshot Metrics
    metrics_summary = _calculate_snapshot_metrics(cleaned_events, window_days)
    
    # 7. Persist Score
    try:
        time_score = TimeScore(
            id=str(uuid.uuid4()),
            user_id=user_id,
            timestamp=datetime.utcnow(),
            
            # Scores
            overall_score=round(overall_score, 1),
            confidence=round(_calculate_confidence(cleaned_events, window_days), 2),
            
            structure_score=round(structure_metric, 1),
            load_score=round(load_metric, 1),
            focus_score=round(focus_metric, 1),
            friction_score=round(friction_metric, 1),
            stress_score=round(stress_metric, 1),
            
            # Metadata
            time_window=f"last_{window_days}_days",
            data_sources_json={"calendar": True, "event_count": len(cleaned_events)},
            
            # Snapshot Metrics
            total_scheduled_hours=round(metrics_summary["total_hours"], 1),
            total_meeting_hours=round(metrics_summary["meeting_hours"], 1),
            total_focus_hours=round(metrics_summary["focus_hours"], 1),
            avg_events_per_day=round(metrics_summary["avg_events"], 1)
        )
        
        db.add(time_score)
        db.commit()
        db.refresh(time_score)
        logger.info(f"TimeScore persisted for user {user_id}: {overall_score}")
        return time_score
        
    except Exception as e:
        logger.error(f"Failed to persist TimeScore: {e}")
        db.rollback()
        return None

# --- Helper Functions ---

def _preprocess_events(events: List[CalendarEvent]) -> List[CalendarEvent]:
    """Filter duplicates, all-day events, and normalize overlaps."""
    cleaned = []
    seen_signatures = set()
    
    for e in events:
        # 1. Skip if missing times
        if not e.start_time or not e.end_time:
            continue
            
        # 2. Skip All-Day (often > 23 hours or exact midnight-midnight)
        duration = (e.end_time - e.start_time).total_seconds()
        if duration >= 86000: # Slightly less than 24h
            continue
            
        # 3. Deduplication (simple signature)
        sig = f"{e.start_time}-{e.end_time}-{e.title}"
        if sig in seen_signatures:
            continue
        seen_signatures.add(sig)
        
        cleaned.append(e)
        
    return sorted(cleaned, key=lambda x: x.start_time)

def _calculate_structure(events: List[CalendarEvent], window_days: int) -> float:
    """
    Structure Score: Regularity of start/end times and consistency.
    Replaces 'Planning Habit' and 'Weekly Rhythm'.
    """
    if not events: return 0.0
    
    # Consistency of "Day Start"
    # Group by date
    days = {}
    for e in events:
        d = e.start_time.date()
        if d not in days: days[d] = []
        days[d].append(e)
        
    if len(days) < 2: return 50.0 # Not enough data
    
    # Calculate start hour variance
    start_hours = []
    for d, daily_events in days.items():
        first_event = min(daily_events, key=lambda x: x.start_time)
        start_hours.append(first_event.start_time.hour + first_event.start_time.minute/60.0)
        
    # Standard deviation of start time
    avg_start = sum(start_hours) / len(start_hours)
    variance = sum((x - avg_start) ** 2 for x in start_hours) / len(start_hours)
    std_dev = variance ** 0.5
    
    # Score: Lower std_dev is better. 
    # 0h dev = 100, 2h dev = 50, >4h dev = 0
    consistency_score = max(0, 100 - (std_dev * 25))
    
    return consistency_score

def _calculate_load(events: List[CalendarEvent], window_days: int) -> float:
    """
    Load Score: Healthy balance of working hours.
    Penalizes both under-working (no data) and over-working (burnout).
    """
    total_duration_hours = sum((e.end_time - e.start_time).total_seconds() for e in events) / 3600
    avg_hours_per_day = total_duration_hours / window_days # Denominator is window, not active days
    
    # Ideal: 6-9 hours per day (assuming weekdays, but window_days filters all)
    # We'll be lenient given weekends exist.
    # Target: 30-50 hours/week => ~4-7 hours/day average over 30 days
    
    if avg_hours_per_day > 10: # Burnout territory
        return max(0, 100 - (avg_hours_per_day - 10) * 10)
    elif avg_hours_per_day < 1: # No data / usage
        return 20.0 
    else:
        # Sweet spot
        return 85.0 + min(15, (avg_hours_per_day / 5) * 15)

def _calculate_focus(events: List[CalendarEvent]) -> float:
    """
    Focus Score: Percentage of time spent in deep work (non-meeting blocks > 1h).
    Using DURATION share, not event count.
    """
    total_time = sum((e.end_time - e.start_time).total_seconds() for e in events)
    if total_time == 0: return 0.0
    
    focus_time = 0
    
    for e in events:
        dur = (e.end_time - e.start_time).total_seconds()
        # Criteria: Not a meeting AND > 45 mins (accepted deep work min)
        # Note: 'is_meeting' field reliability depends on provider. 
        if not e.is_meeting and dur >= 2700: 
            focus_time += dur
            
    ratio = focus_time / total_time
    # Data check: If ratio is 0, user might not label meetings.
    
    # Score: 30% focus time is considered excellent.
    score = min(100, (ratio / 0.30) * 100)
    return score

def _calculate_friction(events: List[CalendarEvent]) -> float:
    """
    Friction Score: Penalizes fragmented time and context switching.
    Analyses gaps between events.
    """
    if len(events) < 2: return 100.0
    
    gaps = []
    for i in range(len(events) - 1):
        e1 = events[i]
        e2 = events[i+1]
        
        # Only check same-day transitions
        if e1.end_time.date() != e2.start_time.date():
            continue
            
        gap = (e2.start_time - e1.end_time).total_seconds()
        
        # Overlapping events: ignore (or treat as double-book friction?)
        if gap < 0: continue
        
        gaps.append(gap)
        
    if not gaps: return 100.0
    
    # "Bad" gaps are those between 15 mins and 1 hour (awkward dead time)
    awkward_gaps = sum(1 for g in gaps if 900 <= g <= 3600)
    
    # Calculate friction ratio
    friction_ratio = awkward_gaps / len(events)
    
    # Score: 0 friction = 100. 20% events causing friction = 50.
    return max(0, 100 - (friction_ratio * 250))

def _calculate_stress(events: List[CalendarEvent], window_days: int) -> float:
    """
    Stress Score: Based on density, back-to-back meetings, and long continuous blocks without breaks.
    """
    stress_points = 0
    total_meeting_seconds = 0
    days_with_events = set()
    
    current_streak = 0
    
    for i in range(len(events)):
        e = events[i]
        days_with_events.add(e.start_time.date())
        
        dur = (e.end_time - e.start_time).total_seconds()
        if e.is_meeting:
            total_meeting_seconds += dur
            
        # Check back-to-back with next event
        if i < len(events) - 1:
            next_e = events[i+1]
            gap = (next_e.start_time - e.end_time).total_seconds()
            if 0 <= gap < 300: # < 5 mins gap
                current_streak += 1
            else:
                if current_streak >= 3: # 3+ back to back meetings
                    stress_points += (current_streak * 2)
                current_streak = 0
                
    # Meeting Density Stress
    avg_meeting_hours = (total_meeting_seconds / 3600) / max(1, len(days_with_events))
    if avg_meeting_hours > 5: stress_points += 20
    elif avg_meeting_hours > 3: stress_points += 10
    
    # Score: Start at 100, subtract stress
    return max(0, 100 - stress_points)

def _calculate_snapshot_metrics(events: List[CalendarEvent], window_days: int) -> Dict[str, float]:
    total_seconds = sum((e.end_time - e.start_time).total_seconds() for e in events)
    meeting_seconds = sum((e.end_time - e.start_time).total_seconds() for e in events if e.is_meeting)
    focus_seconds = sum((e.end_time - e.start_time).total_seconds() for e in events if not e.is_meeting and (e.end_time - e.start_time).total_seconds() >= 2700)
    
    return {
        "total_hours": total_seconds / 3600,
        "meeting_hours": meeting_seconds / 3600,
        "focus_hours": focus_seconds / 3600,
        "avg_events": len(events) / window_days
    }

def _calculate_confidence(events: List[CalendarEvent], window_days: int) -> float:
    """
    Confidence Score (0.0 - 1.0)
    Based on data volume and regularity.
    """
    if not events: return 0.0
    
    unique_days = len(set(e.start_time.date() for e in events))
    coverage = unique_days / window_days
    
    if coverage > 0.7: return 0.9  # High confidence
    if coverage > 0.4: return 0.7  # Medium
    return 0.4 # Low
