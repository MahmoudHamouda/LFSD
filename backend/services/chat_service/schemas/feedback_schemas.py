"""
Feedback Schemas - Pydantic models for validation and serialization.

Replaces the previous Marshmallow schemas for consistency with the rest of the FastAPI application.
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class FeedbackCreate(BaseModel):
    """Schema for creating new feedback."""
    
    message_id: str = Field(..., description="Message ID this feedback relates to")
    feedback: str = Field(..., min_length=1, max_length=500, description="Feedback content")
    

class FeedbackResponse(BaseModel):
    """Schema for feedback responses."""
    
    id: int = Field(..., description="Feedback ID")
    message_id: str = Field(..., description="Related message ID")
    user_id: str = Field(..., description="User who submitted feedback")
    feedback: str = Field(..., description="Feedback content")
    created_at: datetime = Field(..., description="When feedback was created")
    
    class Config:
        from_attributes = True  # Pydantic v2 (was orm_mode in v1)


class FeedbackListResponse(BaseModel):
    """Schema for paginated feedback list."""
    
    items: list[FeedbackResponse]
    total: int
    page: int
    per_page: int
    has_more: bool
