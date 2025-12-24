from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from models.models import User
from services.health_data_fusion import get_health_metrics

# ============================================================================
# Helpers
# ============================================================================

def _normalize_score(value: float, min_val: float, max_val: float, min_score: float = 0, max_score: float = 25) -> float:
    try:
        if value is None: return 0
        if value <= min_val: return min_score
        if value >= max_val: return max_score
        ratio = (value - min_val) / (max_val - min_val)
        return min_score + ratio * (max_score - min_score)
    except:
        return 0

# ============================================================================
# Core Scoring Engine
# ============================================================================

def compute_health_score(user_id: str, db: Session, override_input: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Computes a comprehensive Health Score (0-100) based on 5 pillars.
    Uses fused data from WHOOP, Apple, Google, and Manual inputs.
    """
    try:
        # 1. Fetch Fused Data
        try:
            fused_data = get_health_metrics(user_id, db, period_days=30)
            metrics = fused_data.get("metrics", {})
            profile = fused_data.get("profile", {})
        except:
             metrics = {}
             profile = {}
        
        # Fallback to User Profile/Onboarding if HealthProfile is empty
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if user and user.profile_json:
                db_onboarding = user.profile_json.get("onboarding_data", {})
            else:
                db_onboarding = {}
        except:
            db_onboarding = {}
        
        # Use override input (from API payload) if provided, otherwise DB
        onboarding = override_input if override_input else db_onboarding
        if not onboarding: onboarding = {}
        
        def get_profile_val(key, fallback_key, default):
            # Profiler (DB) > Onboarding Payload > Default
            return profile.get(key) or onboarding.get(fallback_key, default)

        inputs = {
            # A) Sleep
            "sleep_hours_str": onboarding.get("sleep_hours", "7-8"), 
            "sleep_consistency": onboarding.get("sleep_consistency", "Mostly"), 
            "wake_tired": onboarding.get("wake_tired", "Sometimes"), 
            
            # B) Activity
            "activity_level": get_profile_val("activity_level", "activity_level", "Moderate"),
            "activity_type": onboarding.get("activity_type", "None"), 
            
            # C) Recovery
            "stress_level": get_profile_val("stress_level", "stress_level", "Sometimes"),
            "energy_pattern": get_profile_val("energy_pattern", "energy_pattern", "Stable"),
            
            # D) Nutrition
            "diet_style": get_profile_val("diet_style", "diet_style", "Balanced"),
            "water_intake": get_profile_val("water_intake", "water_intake", "1-2L"),
            "smoking": get_profile_val("smoking", "smoking_pattern", "Never"),
            "alcohol": get_profile_val("alcohol", "alcohol_pattern", "Occasionally"),
            
            # E) Lifestyle
            "eating_out_freq": onboarding.get("eating_out_frequency", "Rarely"),
            "takeaway_freq": onboarding.get("takeaway_frequency", "Rarely"),
            "cooking_freq": onboarding.get("cooking_frequency", "Rarely"),
            "nightlife_freq": onboarding.get("nightlife_frequency", "Rarely")
        }

        # Helper to parse sleep range
        def parse_sleep_hours(range_str):
            if not range_str: return 7.5
            if "<5" in range_str: return 4.5
            if "5-6" in range_str: return 5.5
            if "6-7" in range_str: return 6.5
            if "7-8" in range_str: return 7.5
            if "8-9" in range_str: return 8.5
            if ">9" in range_str: return 9.5
            try: return float(range_str) # Fallback if direct number passed
            except: return 7.5

        # 2. Compute Pillars
        
        # --- Pillar 1: Sleep (25%) ---
        # 1. Duration (15 pts)
        sleep_meta = metrics.get("avg_sleep_minutes", {"value": 0, "confidence": 0})
        avg_sleep_min = sleep_meta.get("value", 0)
        
        val_hours = avg_sleep_min / 60 if avg_sleep_min > 0 else parse_sleep_hours(inputs["sleep_hours_str"])
        
        score_duration = 0
        if 7 <= val_hours <= 9: score_duration = 15
        elif 6 <= val_hours < 7 or 9 < val_hours <= 10: score_duration = 10
        elif 5 <= val_hours < 6: score_duration = 5
        else: score_duration = 2
        
        # 2. Consistency (5 pts)
        score_cons = 0
        cons = inputs.get("sleep_consistency", "Mostly")
        if cons == "Consistent": score_cons = 5
        elif cons == "Mostly": score_cons = 3
        else: score_cons = 1
        
        # 3. Wake Tired (5 pts)
        score_wake = 0
        wake = inputs.get("wake_tired", "Sometimes")
        if wake == "No": score_wake = 5
        elif wake == "Sometimes": score_wake = 3
        else: score_wake = 1
        
        sleep_score = score_duration + score_cons + score_wake
        sleep_conf = sleep_meta.get("confidence", 0.5) if avg_sleep_min > 0 else 0.5
            
        # --- Pillar 2: Movement (25%) ---
        step_meta = metrics.get("avg_daily_steps", {"value": 0, "confidence": 0})
        avg_steps = step_meta.get("value", 0)
        
        score_vol = 0
        if avg_steps > 0:
            if avg_steps >= 10000: score_vol = 15
            elif avg_steps >= 7500: score_vol = 12
            elif avg_steps >= 5000: score_vol = 8
            elif avg_steps >= 3000: score_vol = 5
            else: score_vol = 2
        else:
            lvl = inputs.get("activity_level", "Moderate")
            if lvl == "High": score_vol = 15
            elif lvl == "Moderate": score_vol = 10
            elif lvl == "Lightly active": score_vol = 6
            else: score_vol = 2
            
        active_meta = metrics.get("avg_active_minutes", {"value": 0, "confidence": 0})
        avg_active = active_meta.get("value", 0)
        
        score_int = 0
        if avg_active > 0:
            if avg_active >= 30: score_int = 10
            elif avg_active >= 15: score_int = 6
            else: score_int = 3
        else:
            atype = inputs.get("activity_type", "None")
            if atype in ["Running", "Sports", "Gym"]: score_int = 10
            elif atype in ["Yoga", "Walking"]: score_int = 6
            elif atype == "None": score_int = 0
            else: score_int = 5

        movement_score = score_vol + score_int
        movement_conf = step_meta.get("confidence", 0.5) if avg_steps > 0 else 0.5
            
        # --- Pillar 3: Recovery & Stress (20%) ---
        score_stress = 0
        sl = inputs.get("stress_level", "Sometimes")
        if sl == "Rarely": score_stress = 10
        elif sl == "Sometimes": score_stress = 7
        elif sl == "Often": score_stress = 4
        else: score_stress = 1
        
        score_energy = 0
        en = inputs.get("energy_pattern", "Stable")
        if en == "Stable": score_energy = 10
        elif en == "Highs & lows": score_energy = 6
        elif en == "Afternoon crash": score_energy = 5
        else: score_energy = 2
        
        rhr_meta = metrics.get("resting_hr_bpm", {"value": 0, "confidence": 0})
        recovery_score = score_stress + score_energy
        if rhr_meta.get("value", 0) > 0:
            if rhr_meta["value"] < 60: recovery_score = min(20, recovery_score + 2)
            elif rhr_meta["value"] > 80: recovery_score = max(0, recovery_score - 2)
            
        recovery_conf = (sleep_conf + rhr_meta.get("confidence", 0.5)) / 2 if rhr_meta.get("value", 0) > 0 else 0.5
        
        # --- Pillar 4: Nutrition & Habits (20%) ---
        score_diet = 0
        ds = inputs.get("diet_style", "Balanced")
        if ds in ["Balanced", "Mediterranean"]: score_diet = 6
        elif ds in ["Vegetarian", "Vegan", "High-protein"]: score_diet = 5
        elif ds == "High-carb": score_diet = 3
        else: score_diet = 1 
        
        score_water = 0
        wi = inputs.get("water_intake", "1-2L")
        if wi == "3L+": score_water = 4
        elif wi == "2-3L": score_water = 4
        elif wi == "1-2L": score_water = 3
        else: score_water = 1
        
        score_smoke = 0
        sp = inputs.get("smoking", "Never")
        if sp == "Never": score_smoke = 5
        elif sp == "Occasionally": score_smoke = 2
        else: score_smoke = 0
        
        score_alc = 0
        ap = inputs.get("alcohol", "Occasionally")
        if ap == "Never": score_alc = 5
        elif ap == "Occasionally": score_alc = 3
        else: score_alc = 1
        
        nutrition_score = score_diet + score_water + score_smoke + score_alc
        nutrition_conf = 0.6
        
        # --- Pillar 5: Lifestyle Load (10%) ---
        def freq_score(val, is_good_habit=False):
            if is_good_habit: 
                if val == "Daily": return 2.5
                if val == "3-5x week": return 2.0
                if val == "1-2x week": return 1.0
                return 0
            else: 
                if val == "Rarely": return 2.5
                if val == "1-2x week": return 1.5
                if val == "3-5x week": return 0.5
                return 0

        s_eat_out = freq_score(inputs.get("eating_out_freq", "Rarely"), False)
        s_takeaway = freq_score(inputs.get("takeaway_freq", "Rarely"), False)
        s_cooking = freq_score(inputs.get("cooking_freq", "Rarely"), True)
        s_nightlife = freq_score(inputs.get("nightlife_freq", "Rarely"), False)
        
        lifestyle_score = s_eat_out + s_takeaway + s_cooking + s_nightlife
        lifestyle_conf = 0.6
        
        # 3. Overall Score
        overall_score = sleep_score + movement_score + recovery_score + nutrition_score + lifestyle_score
        overall_conf = (sleep_conf + movement_conf + recovery_conf + nutrition_conf + lifestyle_conf) / 5
        
        band = "Needs Attention"
        if overall_score >= 80: band = "Optimal"
        elif overall_score >= 60: band = "Good"
        elif overall_score >= 40: band = "Fair"
        
        return {
            "health_score": round(overall_score, 1),
            "confidence": round(overall_conf, 2),
            "band": band,
            "dimensions": {
                "sleep": {"score": round(sleep_score, 1), "confidence": round(sleep_conf, 2), "max": 25},
                "movement": {"score": round(movement_score, 1), "confidence": round(movement_conf, 2), "max": 25},
                "recovery": {"score": round(recovery_score, 1), "confidence": round(recovery_conf, 2), "max": 20},
                "nutrition": {"score": round(nutrition_score, 1), "confidence": round(nutrition_conf, 2), "max": 20},
                "lifestyle": {"score": round(lifestyle_score, 1), "confidence": round(lifestyle_conf, 2), "max": 10}
            }
        }
    except Exception as e:
        import traceback
        print(f"Health Scoring Error: {e}")
        # Return fallback
        return {
            "health_score": 50.0,
            "confidence": 0.0,
            "band": "Unknown",
            "dimensions": {
                "sleep": {"score": 10, "confidence": 0, "max": 25},
                "movement": {"score": 10, "confidence": 0, "max": 25},
                "recovery": {"score": 10, "confidence": 0, "max": 20},
                "nutrition": {"score": 10, "confidence": 0, "max": 20},
                "lifestyle": {"score": 5, "confidence": 0, "max": 10}
            }
        }

# Adapter for wrapper compatibility with old signature if needed
def calculate_health_score(user_id: str, onboarding_data: Dict[str, Any], db: Session) -> Dict[str, Any]:
    """Wrapper to maintain backward compatibility with api_routes_scores.py"""
    result = compute_health_score(user_id, db, override_input=onboarding_data)
    
    return {
        "score": result["health_score"],
        "subscores": {
            "sleep": result["dimensions"]["sleep"]["score"],
            "activity": result["dimensions"]["movement"]["score"],
            "nutrition": result["dimensions"]["nutrition"]["score"],
            "recovery": result["dimensions"]["recovery"]["score"], 
            "lifestyle": result["dimensions"]["lifestyle"]["score"]
        },
        "data_source": "hybrid" if result["confidence"] > 0.6 else "manual",
        "details": result 
    }
