from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Any, List

from models.database import get_db
from models.models import User, TimeProfile, TimeEvent
from services.time_scoring import compute_time_score
from services.time_data_fusion import get_time_metrics

router = APIRouter(prefix="/time", tags=["time"])

# 1. Manual Inputs
@router.post("/users/{user_id}/manual")
async def save_manual_time_profile(user_id: str, profile_data: Dict[str, Any], db: Session = Depends(get_db)):
    """Save manual time & productivity inputs."""
    # Check user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Upsert TimeProfile
    time_profile = db.query(TimeProfile).filter(TimeProfile.user_id == user_id).first()
    if not time_profile:
        time_profile = TimeProfile(user_id=user_id)
        db.add(time_profile)
    
    # Update fields
    # A) Use the dictionary directly map keys to columns
    allowed_keys = [
        "work_status", "work_hours_per_week", "uses_digital_calendar", "commute_duration",
        "time_meals_house_daily", "time_admin_weekly", "routine_style", "task_style", "time_overwhelm_level"
    ]
    
    for key in allowed_keys:
        if key in profile_data:
            setattr(time_profile, key, profile_data[key])
            
    if "main_time_drains" in profile_data:
        time_profile.main_time_drains = profile_data["main_time_drains"]
        
    time_profile.updated_at = datetime.utcnow()
    db.commit()
    
    return {"status": "success", "message": "Time profile updated"}


# 2. Google Calendar Integration
@router.post("/users/{user_id}/calendar/google/connect")
async def connect_google_calendar(user_id: str):
    """Start Google Calendar OAuth flow."""
    from services.google_calendar_service import GoogleCalendarService
    # We don't have the db session here in the signature, let's add it or just instantiate the service if it handles it?
    # Actually, the service needs DB. Let's redirect to a frontend callback page that calls backend.
    
    # Actually, we need to return the Auth URL so frontend can redirect user.
    # Service initialization requires DB, but `get_auth_url` doesn't strictly need it if we pass nothing.
    # But let's stick to pattern.
    
    # We need to construct the URL manually if we don't want to instantiate the service with DB just for this.
    # But let's check the service definition. It takes `db`.
    pass 

@router.get("/users/{user_id}/calendar/google/connect")
async def get_google_auth_url(user_id: str, db: Session = Depends(get_db)):
    """Get the Google Auth URL."""
    from services.google_calendar_service import GoogleCalendarService
    service = GoogleCalendarService(db)
    # We can pass user_id as state
    url = service.get_auth_url(state=user_id)
    return {"auth_url": url}

@router.get("/users/{user_id}/calendar/google/callback")
async def google_auth_callback(user_id: str, code: str, db: Session = Depends(get_db)):
    """Handle OAuth callback."""
    from services.google_calendar_service import GoogleCalendarService
    service = GoogleCalendarService(db)
    connection = service.exchange_code(code, user_id)
    return {"status": "success", "message": "Google Calendar connected"}

@router.get("/users/{user_id}/calendar/google/sync")
async def sync_google_calendar(user_id: str, db: Session = Depends(get_db)):
    """Fetch events from Google Calendar."""
    from services.google_calendar_service import GoogleCalendarService
    service = GoogleCalendarService(db)
    try:
        count = service.fetch_events(user_id)
        return {"status": "success", "message": f"Synced {count} events"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/users/{user_id}/calendar/upload")
async def upload_calendar_screenshot(user_id: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload and parse calendar screenshot/PDF."""
    try:
        from PIL import Image
        import pytesseract
        import io
        
        # 1. Read Image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # 2. Extract Text via OCR
        # Explicitly set path for Windows
        pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
        text = pytesseract.image_to_string(image)
        
        if not text or len(text) < 10:
             raise HTTPException(status_code=400, detail="Could not extract text from image. Please ensure it is clear.")
             
        # 3. Parse Text into Events using Gemini (LLM)
        from services.gemini_service import GeminiService
        gemini = GeminiService(db) # We might need to adjust init if it does heavy loading
        
        # Construct Prompt for Parsing
        prompt = f"""
        Extract calendar events from the following OCR text.
        Return a JSON list of objects associated with the events.
        Each object should have: title, start_time (ISO format), end_time (ISO format), category (Work/Personal/etc).
        Assume the current year is {datetime.now().year}.
        
        OCR Text:
        {text}
        """
        
        # We need a method in GeminiService to run raw prompt
        # Assuming `model.generate_content` is accessible or we wrap it.
        # Let's use `_extract_intent` or similar? No, that's for chat.
        # We'll validly access the model directly or add a helper.
        
        response = gemini.model.generate_content(prompt)
        import json
        
        cleaned_text = response.text.replace("```json", "").replace("```", "").strip()
        events_data = json.loads(cleaned_text)
        
        if not isinstance(events_data, list):
            events_data = [events_data] # Handle single object return
            
        count = 0
        for e_data in events_data:
            try:
                # Basic validation
                if not e_data.get('start_time'): continue
                
                event = TimeEvent(
                   user_id=user_id,
                   source="screenshot_upload",
                   title=e_data.get('title', 'Unknown Event'),
                   start_time=datetime.fromisoformat(e_data['start_time'].replace("Z", "+00:00")),
                   end_time=datetime.fromisoformat(e_data['end_time'].replace("Z", "+00:00")),
                   category=e_data.get('category', 'Uncategorized')
                )
                
                # Calculate duration
                diff = event.end_time - event.start_time
                event.duration_minutes = int(diff.total_seconds() / 60)
                
                db.add(event)
                count += 1
            except Exception as e:
                print(f"Skipping event due to parse error: {e}")
                continue
                
        db.commit()
    
        return {"status": "success", "message": f"Parsed {count} events from screenshot"}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        # Log to file for easier debugging
        with open("error_log.txt", "a") as f:
             f.write(f"OCR Error: {str(e)}\n\n")
             traceback.print_exc(file=f)
        raise HTTPException(status_code=500, detail=f"OCR Failed: {str(e)}")

from core.authentication import get_current_user

# 5. Get Events Endpoint (Session-based)
@router.get("/events")
async def get_time_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all calendar events for the logged-in user."""
    from models.models import CalendarEvent
    events = db.query(CalendarEvent).filter(CalendarEvent.user_id == current_user.id).all()
    
    return {
        "status": "success",
        "data": [
            {
                "id": e.id,
                "title": e.title,
                "start": e.start_time,
                "end": e.end_time,
                "category": "Meeting" if getattr(e, "is_meeting", False) else "Work",
                "is_all_day": False
            }
            for e in events
        ]
    }

# 4. Time Score Endpoint
@router.get("/users/{user_id}/score")
async def get_time_score(user_id: str, db: Session = Depends(get_db)):
    """Get Time & Productivity Score and Breakdown."""
    
    score_data = compute_time_score(user_id, db)
    metrics_data = get_time_metrics(user_id, db)
    
    # Generate Mock Recommendations based on score
    recommendations = []
    dims = score_data["dimensions"]
    
    if dims["structure"]["score"] < 15:
        recommendations.append("High Impact: Try putting your key tasks in a simple daily calendar block.")
    if dims["load"]["score"] < 15:
        recommendations.append("Your days are very full. Consider protecting 1–2 meeting-free hours.")
    if dims["friction"]["score"] < 10:
        recommendations.append("You spend a lot of time on admin. We can help automate bills & errands.")
    if dims["stress"]["score"] < 10:
        recommendations.append("You often feel short on time. Let's start by freeing 30–60 minutes a week.")
        
    return {
        "status": "success",
        "data": {
            "overall": {
                "score": score_data["productivity_score"],
                "confidence": score_data["confidence"],
                "band": score_data["band"]
            },
            "dimensions": dims,
            "metrics_used": metrics_data["metrics"],
            "recommendations": recommendations
        }
    }
