from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from services.time_data_fusion import get_time_metrics
from loguru import logger

def compute_time_score(user_id: str, db: Session, override_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Computes Time & Productivity Score (0-100).
    """
    try:
        # 1. Fetch Data
        try:
            data = get_time_metrics(user_id, db)
            metrics = data.get("metrics", {})
            profile = data.get("profile", {})
        except:
            metrics = {}
            profile = {}
        
        if override_input:
            # Updates existing keys and adds new ones
            profile.update(override_input)
                        
            # Re-calc derived metrics if needed 
            commute_map = {"No commute": 0, "<15 min": 15, "15-30 min": 22, "30-60 min": 45, "60+": 75}
            if "commute_duration" in override_input:
                val = commute_map.get(override_input["commute_duration"], 30)
                if "commute_minutes_per_day" in metrics:
                    metrics["commute_minutes_per_day"]["value"] = val
                else:
                    metrics["commute_minutes_per_day"] = {"value": val, "confidence": 0.5}
                
            admin_map = {"<1 hour": 0.5, "1-3 hours": 2, "3-5 hours": 4, "5+ hours": 6}
            if "time_admin_weekly" in override_input:
                val = admin_map.get(override_input["time_admin_weekly"], 2)
                if "admin_hours_per_week" in metrics:
                     metrics["admin_hours_per_week"]["value"] = val
                else:
                     metrics["admin_hours_per_week"] = {"value": val, "confidence": 0.5}

        # Helper for safer metric access
        def get_metric_val(key, default=0):
            return metrics.get(key, {}).get("value", default)

        def get_metric_conf(key, default=0.5):
            return metrics.get(key, {}).get("confidence", default)

        # 2. Compute Pillars (0-100 scales normalized to weights)
        
        # --- Pillar 1: Structure & Planning (25%) ---
        p1_score = 0
        
        cal_usage = get_metric_val("calendar_usage_score", 0.2)
        p1_score += (cal_usage * 10) # Max 10 pts
        
        routine = profile.get("routine_style", "I try")
        if routine == "I follow a routine": p1_score += 8
        elif routine == "I try": p1_score += 5
        elif routine == "I'm spontaneous": p1_score += 3
        else: p1_score += 1 # Not really
        
        task = profile.get("task_style", "I react to what's urgent")
        if task == "I plan ahead": p1_score += 7
        elif task == "I plan but things shift": p1_score += 5
        elif task == "I go with the flow": p1_score += 3
        else: p1_score += 1 # React
        
        structure_score = min(p1_score, 25)
        structure_conf = get_metric_conf("calendar_usage_score")

        # --- Pillar 2: Load & Capacity (25%) ---
        # Fixed: Double counting meeting_hours was removed from Pillar 3 focus, but kept here for Load.
        p2_score = 25 
        
        work_hrs = get_metric_val("avg_work_hours_per_day", 8)
        if work_hrs > 12: p2_score -= 10
        elif work_hrs > 10: p2_score -= 6
        elif work_hrs > 8.5: p2_score -= 2
        
        meet_hrs = get_metric_val("avg_meeting_hours_per_day", 2)
        if meet_hrs > 6: p2_score -= 8
        elif meet_hrs > 4: p2_score -= 4
        
        commute = get_metric_val("commute_minutes_per_day", 30)
        if commute > 90: p2_score -= 5
        elif commute > 45: p2_score -= 2
        
        load_score = max(5, p2_score)
        load_conf = get_metric_conf("avg_work_hours_per_day", 0.6)

        # --- Pillar 3: Focus & Fragmentation (20%) ---
        p3_score = 20
        
        # Reduced penalty for meetings here to avoid double jeopardy, 
        # focusing only on excessive fragmentation > 4h
        if meet_hrs > 5: p3_score -= 4 
        
        drains = profile.get("main_time_drains", [])
        if isinstance(drains, list):
            if "Meetings" in drains: p3_score -= 2
            if "Emails" in drains: p3_score -= 2
            if "Last-minute tasks" in drains: p3_score -= 3
            
        focus_score = max(5, p3_score)
        focus_conf = 0.6

        # --- Pillar 4: Friction & Admin (15%) ---
        p4_score = 15
        admin_hrs = get_metric_val("admin_hours_per_week", 2)
        
        if admin_hrs > 10: p4_score -= 8 # Only punish extreme admin
        elif admin_hrs > 5: p4_score -= 4
        
        friction_score = max(5, p4_score)
        friction_conf = get_metric_conf("admin_hours_per_week", 0.6)

        # --- Pillar 5: Stress & Overwhelm (15%) ---
        p5_score = 15
        overwhelm = metrics.get("time_overwhelm_level", {}).get("value", "Sometimes")
        
        if overwhelm == "Almost always": p5_score -= 8
        elif overwhelm == "Often": p5_score -= 5
        elif overwhelm == "Sometimes": p5_score -= 2
        # Rarely = 0 deduction
        
        stress_score = max(5, p5_score)
        stress_conf = get_metric_conf("time_overwhelm_level", 0.6)

        # --- Overall ---
        overall_score = structure_score + load_score + focus_score + friction_score + stress_score
        overall_conf = (structure_conf + load_conf + focus_conf + friction_conf + stress_conf) / 5
        
        band = "Stretched"
        if overall_score >= 80: band = "Flow State"
        elif overall_score >= 60: band = "Balanced"
        elif overall_score >= 40: band = "Manageable"
        
        return {
            "productivity_score": round(overall_score, 1),
            "confidence": round(overall_conf, 2),
            "band": band,
            "dimensions": {
                "structure": {"score": round(structure_score, 1), "max": 25},
                "load": {"score": round(load_score, 1), "max": 25},
                "focus": {"score": round(focus_score, 1), "max": 20},
                "friction": {"score": round(friction_score, 1), "max": 15},
                "stress": {"score": round(stress_score, 1), "max": 15}
            }
        }
    except Exception as e:
        import traceback
        logger.error(f"Time Scoring Error: {e}")
        return {
            "productivity_score": 50.0,
            "confidence": 0.0,
            "band": "Unknown",
            "dimensions": {
                "structure": {"score": 12.5, "max": 25},
                "load": {"score": 12.5, "max": 25},
                "focus": {"score": 10, "max": 20},
                "friction": {"score": 7.5, "max": 15},
                "stress": {"score": 7.5, "max": 15}
            }
        }

def calculate_productivity_score(user_id: str, onboarding_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Wrapper for API compatibility."""
    result = compute_time_score(user_id, db, override_input=onboarding_data)
    
    return {
        "score": result["productivity_score"],
        "subscores": {k: v["score"] for k, v in result["dimensions"].items()},
        "details": result
    }
