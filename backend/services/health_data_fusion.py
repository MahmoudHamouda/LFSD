from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from models.models import HealthDataSample, HealthProfile
import json
from loguru import logger

# ============================================================================
# Helpers
# ============================================================================


def _calculate_confidence(
    sources: List[str], metric_type: str, sample_count: int = 0
) -> float:
    """
    Calculate confidence based on source quality and data density.
    """
    if not sources:
        return 0.0

    has_whoop = "whoop" in sources
    has_wearable = "apple_health" in sources or "google_fit" in sources
    has_manual = "manual" in sources

    base_conf = 0.5

    if metric_type in ["sleep", "recovery"]:
        if has_whoop:
            base_conf = 0.95
        elif has_wearable:
            base_conf = 0.85
        else:
            base_conf = 0.5

    elif metric_type == "activity":
        if has_wearable:
            base_conf = 0.90
        elif has_whoop:
            base_conf = 0.85
        else:
            base_conf = 0.4

    elif metric_type == "habits":
        base_conf = 0.6  # Self-report mostly

    # Penalty for sparse data (e.g. only 2 days of data in 30 day window)
    # We assume 'sample_count' is passed (number of days with data)
    # For now, if we don't have sample_count pushed down, we leave as is,
    # but the caller logic below does aggregation so we can improve this later.
    return base_conf


def _get_metric_samples(
    samples: List[HealthDataSample], metric_attr: str
) -> List[tuple]:
    """Extract (value, source) tuples for a metric."""
    values = []
    for s in samples:
        val = getattr(s, metric_attr, None)
        if val is not None and val > 0:
            values.append((float(val), s.source))
    return values


def _fuse_metric(
    samples: List[HealthDataSample], metric_attr: str, metric_type: str
) -> Dict[str, Any]:
    """
    Fuse a specific metric from multiple samples using precedence rules.
    Precedence: WHOOP > Apple/Google > Manual (generally).
    For activity: Apple/Google > WHOOP > Manual.
    """
    data = _get_metric_samples(samples, metric_attr)
    if not data:
        return {"value": 0, "sources": [], "confidence": 0.0}

    # Group by source
    by_source = {}
    for val, src in data:
        if src not in by_source:
            by_source[src] = []
        by_source[src].append(val)

    # Calculate averages per source
    avgs = {src: sum(vals) / len(vals) for src, vals in by_source.items()}
    sources_present = list(avgs.keys())

    selected_val = 0.0
    used_sources = []

    if metric_type == "sleep":
        # Prefer WHOOP
        if "whoop" in avgs:
            selected_val = avgs["whoop"]
            used_sources = ["whoop"]
        elif "apple_health" in avgs:  # or google
            selected_val = avgs.get("apple_health", avgs.get("google_fit", 0))
            used_sources = [s for s in ["apple_health", "google_fit"] if s in avgs]
        else:
            selected_val = avgs.get("manual", 0)
            used_sources = ["manual"]

    elif metric_type == "activity":
        # Prefer Steps from Apple/Google
        # If both exist, take max (often one device captures walks, other captures runs?) or avg?
        # Typically max is safer for 'steps' if devices aren't syncing.
        # But 'averaging' reduces noise. Let's use avg for consistency.
        if "apple_health" in avgs or "google_fit" in avgs:
            vals = [avgs[s] for s in ["apple_health", "google_fit"] if s in avgs]
            selected_val = sum(vals) / len(vals)
            used_sources = [s for s in ["apple_health", "google_fit"] if s in avgs]
        elif "whoop" in avgs:
            selected_val = avgs["whoop"]
            used_sources = ["whoop"]
        else:
            selected_val = avgs.get("manual", 0)
            used_sources = ["manual"]

    else:
        # Default average all
        selected_val = sum(avgs.values()) / len(avgs)
        used_sources = sources_present

    return {
        "value": round(selected_val, 1),
        "sources": used_sources,
        "confidence": _calculate_confidence(used_sources, metric_type),
    }


# ============================================================================
# Main Fusion Logic
# ============================================================================


def get_health_metrics(
    user_id: str, db: Session, period_days: int = 30
) -> Dict[str, Any]:
    """
    Aggregates health data from all sources for the given user.
    """
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=period_days)

        # 1. Fetch Objective Data
        samples = (
            db.query(HealthDataSample)
            .filter(
                HealthDataSample.user_id == user_id, HealthDataSample.date >= start_date
            )
            .all()
        )

        # 2. Fetch Aggregated Profile
        profile = (
            db.query(HealthProfile).filter(HealthProfile.user_id == user_id).first()
        )

        # 3. Fuse Metrics

        # Sleep
        sleep_mins = _fuse_metric(samples, "sleep_minutes", "sleep")

        # Activity
        steps = _fuse_metric(samples, "steps", "activity")
        active_mins = _fuse_metric(samples, "active_minutes", "activity")

        # Recovery (HRV/RHR)
        # Note: 'avg_hr_bpm' is NOT HRV. HRV is 'hrv_average' (if available) or specific field.
        # Check HealthDataSample model: it DOES NOT have an explicit HRV column currently shown (only avg_hr_bpm).
        # We must assume metadata_json might hold it, or add the column.
        # For now, we will NOT use avg_hr_bpm as proxy for HRV, as that is wrong.
        # We will iterate RHR as the recovery proxy.
        rhr = _fuse_metric(samples, "resting_hr_bpm", "recovery")

        # 4. Construct Result
        metrics = {
            "avg_sleep_minutes": sleep_mins,
            "avg_daily_steps": steps,
            "avg_active_minutes": active_mins,
            "resting_hr_bpm": rhr,
        }

        profile_data = {}
        if profile:
            profile_data = {
                "diet_style": profile.diet_style,
                "stress_level": profile.stress_level,
                "activity_level": profile.activity_self_report,
                "smoking": profile.smoking_pattern,
                "alcohol": profile.alcohol_pattern,
                "habits": profile.lifestyle_habits_json,
            }

        return {"metrics": metrics, "profile": profile_data}
    except Exception as e:
        logger.error(f"Health fusion error: {e}")
        return {"metrics": {}, "profile": {}, "error": str(e)}
