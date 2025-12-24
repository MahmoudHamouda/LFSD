from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from models.models import HealthDataSample, HealthProfile
import json

# ============================================================================
# Helpers
# ============================================================================

def _calculate_confidence(sources: List[str], metric_type: str) -> float:
    """
    Calculate confidence based on source quality.
    """
    if not sources:
        return 0.0
        
    has_whoop = "whoop" in sources
    has_wearable = "apple_health" in sources or "google_fit" in sources
    has_manual = "manual" in sources
    
    if metric_type in ["sleep", "recovery"]:
        if has_whoop: return 0.95
        if has_wearable: return 0.85
        return 0.5
        
    if metric_type == "activity":
        if has_wearable: return 0.90
        if has_whoop: return 0.85
        return 0.4
        
    if metric_type == "habits":
        return 0.6 # Self-report mostly
        
    return 0.5

def _get_metric_samples(samples: List[HealthDataSample], metric_attr: str) -> List[tuple]:
    """Extract (value, source) tuples for a metric."""
    values = []
    for s in samples:
        val = getattr(s, metric_attr, None)
        if val is not None and val > 0:
            values.append((val, s.source))
    return values

def _fuse_metric(samples: List[HealthDataSample], metric_attr: str, metric_type: str) -> Dict[str, Any]:
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
        if src not in by_source: by_source[src] = []
        by_source[src].append(val)
        
    # Calculate averages per source
    avgs = {src: sum(vals)/len(vals) for src, vals in by_source.items()}
    sources_present = list(avgs.keys())
    
    selected_val = 0
    used_sources = []
    
    if metric_type == "sleep":
        # Prefer WHOOP
        if "whoop" in avgs:
            selected_val = avgs["whoop"]
            used_sources = ["whoop"]
        elif "apple_health" in avgs: # or google
            selected_val = avgs.get("apple_health", avgs.get("google_fit", 0))
            used_sources = [s for s in ["apple_health", "google_fit"] if s in avgs]
        else:
            selected_val = avgs.get("manual", 0)
            used_sources = ["manual"]
            
    elif metric_type == "activity":
        # Prefer Steps from Apple/Google
        if "apple_health" in avgs or "google_fit" in avgs:
             # Average if both exist? Or max? Let's avg for now or pick one.
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
        "value": selected_val,
        "sources": used_sources,
        "confidence": _calculate_confidence(used_sources, metric_type)
    }

# ============================================================================
# Main Fusion Logic
# ============================================================================

def get_health_metrics(user_id: str, db: Session, period_days: int = 30) -> Dict[str, Any]:
    """
    Aggregates health data from all sources for the given user.
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=period_days)
    
    # 1. Fetch Objective Data
    samples = db.query(HealthDataSample).filter(
        HealthDataSample.user_id == user_id,
        HealthDataSample.date >= start_date
    ).all()
    
    # 2. Fetch Aggregated Profile
    profile = db.query(HealthProfile).filter(HealthProfile.user_id == user_id).first()
    
    # 3. Fuse Metrics
    
    # Sleep
    sleep_mins = _fuse_metric(samples, "sleep_minutes", "sleep")
    
    # Activity
    steps = _fuse_metric(samples, "steps", "activity")
    active_mins = _fuse_metric(samples, "active_minutes", "activity")
    
    # Recovery (HRV/RHR) - Prefer WHOOP
    hrv = _fuse_metric(samples, "avg_hr_bpm", "recovery") # Mapping avg_hr to recovery for now, usually needs specific field
    # Note: DB model has resting_hr_bpm, let's use that
    rhr = _fuse_metric(samples, "resting_hr_bpm", "recovery")
    
    # 4. Construct Result
    metrics = {
        "avg_sleep_minutes": sleep_mins,
        "avg_daily_steps": steps,
        "avg_active_minutes": active_mins,
        "resting_hr_bpm": rhr,
        # TODO: Add HRV if we add column for it
    }
    
    profile_data = {}
    if profile:
        profile_data = {
            "diet_style": profile.diet_style,
            "stress_level": profile.stress_level,
            "activity_level": profile.activity_self_report,
            "smoking": profile.smoking_pattern,
            "alcohol": profile.alcohol_pattern,
            "habits": profile.lifestyle_habits_json
        }
    
    return {
        "metrics": metrics,
        "profile": profile_data
    }
