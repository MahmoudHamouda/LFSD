"""
Time Scoring Service
Calculates time management scores based on calendar events and time profile data.
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from models.models import User, CalendarEvent, TimeScore
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


def calculate_time_score(db: Session, user_id: str, window: str = "month") -> Optional[TimeScore]:
    """
    Calculate comprehensive time score for a user based on calendar data.
    
    Args:
        db: Database session
        user_id: User ID
        window: Time window ('week', 'month', 'quarter')
    
    Returns:
        TimeScore object with calculated subscores
    """
    # Determine time window
    window_days = {
        "week": 7,
        "month": 30,
        "quarter": 90
    }.get(window, 30)
    
    start_date = datetime.utcnow() - timedelta(days=window_days)
    
    # Get calendar events for the window
    events = db.query(CalendarEvent).filter(
        CalendarEvent.user_id == user_id,
        CalendarEvent.start_time >= start_date
    ).all()
    
    if not events:
        logger.info(f"No calendar events found for user {user_id}")
        return None
    
    # Calculate subscores
    schedule_coverage = _calculate_schedule_coverage(events, window_days)
    planning_habit = _calculate_planning_habit(events)
    focus_blocks = _calculate_focus_blocks(events)
    meeting_load = _calculate_meeting_load(events)
    context_switching = _calculate_context_switching(events)
    weekly_rhythm = _calculate_weekly_rhythm(events)
    time_alignment = _calculate_time_alignment(events)
    
    # Calculate overall score (weighted average)
    overall_score = (
        schedule_coverage * 0.20 +
        planning_habit * 0.15 +
        focus_blocks * 0.20 +
        meeting_load * 0.15 +
        context_switching * 0.10 +
        weekly_rhythm * 0.10 +
        time_alignment * 0.10
    )
    
    # Calculate snapshot metrics
    total_scheduled_hours = sum(
        (event.end_time - event.start_time).total_seconds() / 3600
        for event in events
    )
    total_meeting_hours = sum(
        (event.end_time - event.start_time).total_seconds() / 3600
        for event in events if event.is_meeting
    )
    total_focus_hours = sum(
        (event.end_time - event.start_time).total_seconds() / 3600
        for event in events if not event.is_meeting and (event.end_time - event.start_time).total_seconds() >= 3600
    )
    avg_events_per_day = len(events) / window_days
    
    # Create TimeScore record
    time_score = TimeScore(
        user_id=user_id,
        overall_score=round(overall_score, 1),
        schedule_coverage_score=round(schedule_coverage, 1),
        planning_habit_score=round(planning_habit, 1),
        focus_blocks_score=round(focus_blocks, 1),
        meeting_load_score=round(meeting_load, 1),
        context_switching_score=round(context_switching, 1),
        weekly_rhythm_score=round(weekly_rhythm, 1),
        time_alignment_score=round(time_alignment, 1),
        time_window=f"last_{window_days}_days",
        data_sources_json={"calendar": True, "manual": False},
        total_scheduled_hours=round(total_scheduled_hours, 1),
        total_meeting_hours=round(total_meeting_hours, 1),
        total_focus_hours=round(total_focus_hours, 1),
        avg_events_per_day=round(avg_events_per_day, 1)
    )
    
    return time_score


def _calculate_schedule_coverage(events, window_days: int) -> float:
    """Calculate % of days with scheduled events (0-100)"""
    if not events:
        return 0.0
    
    unique_days = len(set(event.start_time.date() for event in events))
    coverage_ratio = unique_days / window_days
    return min(coverage_ratio * 100, 100)


def _calculate_planning_habit(events) -> float:
    """Calculate consistency of planning ahead (0-100)"""
    if not events:
        return 0.0
    
    # Simple heuristic: if events are spread across multiple days, planning is good
    unique_days = len(set(event.start_time.date() for event in events))
    if unique_days >= 20:
        return 85.0
    elif unique_days >= 10:
        return 70.0
    elif unique_days >= 5:
        return 50.0
    else:
        return 30.0


def _calculate_focus_blocks(events) -> float:
    """Calculate presence of uninterrupted work time (0-100)"""
    if not events:
        return 0.0
    
    # Count events >= 2 hours that are not meetings
    focus_events = [
        e for e in events 
        if not e.is_meeting and (e.end_time - e.start_time).total_seconds() >= 7200
    ]
    
    focus_ratio = len(focus_events) / len(events) if events else 0
    return min(focus_ratio * 100 * 2, 100)  # Amplify for scoring


def _calculate_meeting_load(events) -> float:
    """Calculate meeting load (0-100, higher is better = fewer meetings)"""
    if not events:
        return 100.0
    
    meeting_count = sum(1 for e in events if e.is_meeting)
    meeting_ratio = meeting_count / len(events)
    
    # Inverse scoring: fewer meetings = better score
    return max(100 - (meeting_ratio * 100), 0)


def _calculate_context_switching(events) -> float:
    """Calculate context switching frequency (0-100, higher is better = less switching)"""
    if len(events) <= 1:
        return 100.0
    
    # Sort events by start time
    sorted_events = sorted(events, key=lambda e: e.start_time)
    
    # Count gaps between events (potential context switches)
    gaps = 0
    for i in range(len(sorted_events) - 1):
        gap = (sorted_events[i+1].start_time - sorted_events[i].end_time).total_seconds()
        if 0 < gap < 3600:  # Gap less than 1 hour
            gaps += 1
    
    switch_ratio = gaps / (len(events) - 1) if len(events) > 1 else 0
    return max(100 - (switch_ratio * 100), 0)


def _calculate_weekly_rhythm(events) -> float:
    """Calculate consistency week-to-week (0-100)"""
    if not events:
        return 0.0
    
    # Group events by week
    weeks = {}
    for event in events:
        week_num = event.start_time.isocalendar()[1]
        weeks[week_num] = weeks.get(week_num, 0) + 1
    
    if len(weeks) < 2:
        return 50.0  # Not enough data
    
    # Calculate variance in events per week
    avg_events = sum(weeks.values()) / len(weeks)
    variance = sum((count - avg_events) ** 2 for count in weeks.values()) / len(weeks)
    
    # Lower variance = better rhythm
    if variance < 5:
        return 90.0
    elif variance < 15:
        return 70.0
    else:
        return 50.0


def _calculate_time_alignment(events) -> float:
    """Calculate alignment with priorities (0-100)"""
    # Placeholder: would need priority data to calculate properly
    # For now, return a moderate score
    return 65.0
