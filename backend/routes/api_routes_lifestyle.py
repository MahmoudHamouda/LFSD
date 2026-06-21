from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from models.database import get_db

from services.lifestyle_service import LifestyleService
from core.authentication import get_current_user
from models.models import User

router = APIRouter(prefix="/lifestyle", tags=["lifestyle"])


@router.get("/events", summary="Get upcoming lifestyle events")
async def get_events(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    service = LifestyleService(db)
    return service.get_upcoming_events(current_user.id)


@router.post("/events", summary="Create a lifestyle event")
async def create_event(
    event_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = LifestyleService(db)
    return service.create_event(current_user.id, event_data)


@router.get("/recommendations", summary="Get 'Treat Yourself' recommendations")
async def get_recommendations(
    mood: str = "stress",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = LifestyleService(db)
    return service.get_recommendations(current_user.id, mood)


@router.get("/goals", summary="Get life goals")
async def get_goals(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    service = LifestyleService(db)
    return {"data": service.get_goals(current_user.id)}


@router.post("/goals", summary="Create a life goal")
async def create_goal(
    goal_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    service = LifestyleService(db)
    return service.create_goal(current_user.id, goal_data)
