from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, Any, List
from models.models import User, TimeProfile, TimeEvent
from sqlalchemy import func


def get_time_metrics(
    user_id: str, db: Session, period_days: int = 30
) -> Dict[str, Any]:
    """
    Combines TimeProfile + TimeEvent + (optional mobility) into
    aggregated metrics for the last `period_days`.
    """

    # 1. Fetch Profile
    user = db.query(User).filter(User.id == user_id).first()
    time_profile = db.query(TimeProfile).filter(TimeProfile.user_id == user_id).first()

    if not user:
        return {"metrics": {}, "profile": {}}

    # Fallback to Onboarding Data if TimeProfile missing
    onboarding = (user.profile_json or {}).get("onboarding_data", {})
    productivity_input = onboarding.get("productivity", {})

    # Helper to resolve profile values
    def get_val(attr, input_key, default):
        if time_profile and getattr(time_profile, attr):
            return getattr(time_profile, attr)
        return productivity_input.get(input_key, default)

    profile_data = {
        "work_status": get_val("work_status", "employment_type", "Full-time"),
        "work_hours_per_week": get_val(
            "work_hours_per_week", "work_hours_per_week", "40"
        ),
        "uses_digital_calendar": get_val(
            "uses_digital_calendar", "uses_digital_calendar", "No"
        ),
        "commute_duration": get_val("commute_duration", "commute_duration", "<15 min"),
        "time_meals_house_daily": get_val(
            "time_meals_house_daily", "time_meals_house_daily", "1-2 hours"
        ),
        "time_admin_weekly": get_val(
            "time_admin_weekly", "time_admin_weekly", "1-3 hours"
        ),
        "main_time_drains": get_val("main_time_drains", "main_time_drains", []),
        "routine_style": get_val("routine_style", "routine_style", "I try"),
        "task_style": get_val("task_style", "task_style", "I react to what's urgent"),
        "time_overwhelm_level": get_val(
            "time_overwhelm_level", "time_overwhelm_level", "Sometimes"
        ),
    }

    # 2. Fetch Events
    cutoff_date = datetime.utcnow() - timedelta(days=period_days)
    events = (
        db.query(TimeEvent)
        .filter(TimeEvent.user_id == user_id, TimeEvent.start_time >= cutoff_date)
        .all()
    )

    # 3. Compute Metrics

    # Defaults based on profile
    work_hrs_manual = 40.0
    try:
        raw_wh = str(profile_data["work_hours_per_week"])
        if "<20" in raw_wh:
            work_hrs_manual = 15
        elif "20-35" in raw_wh:
            work_hrs_manual = 27.5
        elif "35-45" in raw_wh:
            work_hrs_manual = 40
        elif "45-55" in raw_wh:
            work_hrs_manual = 50
        elif "55+" in raw_wh:
            work_hrs_manual = 60
        else:
            work_hrs_manual = float(raw_wh)
    except:
        work_hrs_manual = 40.0

    metrics = {
        "avg_work_hours_per_day": {
            "value": work_hrs_manual / 5.0,
            "sources": ["manual"],
            "confidence": 0.5,
        },
        "avg_meeting_hours_per_day": {"value": 0.0, "sources": [], "confidence": 0.0},
        "commute_minutes_per_day": {
            "value": 0.0,
            "sources": ["manual"],
            "confidence": 0.5,
        },
        "admin_hours_per_week": {
            "value": 0.0,
            "sources": ["manual"],
            "confidence": 0.5,
        },
        "calendar_usage_score": {
            "value": 0.0,
            "sources": ["manual"],
            "confidence": 0.5,
        },
        "routine_style": {
            "value": profile_data["routine_style"],
            "sources": ["manual"],
            "confidence": 0.8,
        },
        "time_overwhelm_level": {
            "value": profile_data["time_overwhelm_level"],
            "sources": ["manual"],
            "confidence": 0.9,
        },
    }

    # Integrate Calendar Data if available
    if events:
        total_meeting_mins = 0
        days_with_events = set()

        for e in events:
            # Simple heuristic for now
            if e.category in ["Work", "WorkMeeting"] or (
                e.title and "meeting" in e.title.lower()
            ):
                total_meeting_mins += e.duration_minutes or 0

            days_with_events.add(e.start_time.date())

        num_days = max(1, len(days_with_events))  # Avoid div by zero
        avg_meet_hrs = (total_meeting_mins / 60.0) / num_days

        metrics["avg_meeting_hours_per_day"] = {
            "value": round(avg_meet_hrs, 1),
            "sources": ["google_calendar"],
            "confidence": 0.9,
        }

        # Adjust work hours if calendar shows significant work
        # (This logic is usually more complex, simplified here)
        metrics["avg_work_hours_per_day"]["confidence"] = 0.7  # boost confidence

    # Parse Commute
    commute_map = {
        "No commute": 0,
        "<15 min": 15,
        "15-30 min": 22,
        "30-60 min": 45,
        "60+": 75,
    }
    metrics["commute_minutes_per_day"]["value"] = commute_map.get(
        profile_data["commute_duration"], 30
    )

    # Parse Admin
    admin_map = {"<1 hour": 0.5, "1-3 hours": 2, "3-5 hours": 4, "5+ hours": 6}
    metrics["admin_hours_per_week"]["value"] = admin_map.get(
        profile_data["time_admin_weekly"], 2
    )

    # Calendar Usage Score
    if profile_data["uses_digital_calendar"].startswith("Yes"):
        cal_score = 0.8
        if not events:
            cal_score = 0.4  # Claimed yes but no data
        elif len(events) > 10:
            cal_score = 1.0
        metrics["calendar_usage_score"] = {
            "value": cal_score,
            "sources": ["manual", "data"],
            "confidence": 0.8,
        }
    else:
        metrics["calendar_usage_score"] = {
            "value": 0.2,
            "sources": ["manual"],
            "confidence": 0.9,
        }

    return {"metrics": metrics, "profile": profile_data}
