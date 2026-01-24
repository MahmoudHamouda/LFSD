"""
Feedback Repository - Database access layer using proper dependency injection.

This repository handles feedback data persistence with proper FastAPI patterns:
- Uses injected Session (no global SessionLocal)
- Supports user scoping for authorization
- Provides pagination with clear contracts
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc
from models.chat_models import Feedback
from typing import List, Optional


class FeedbackRepository:
    """
    Repository for feedback operations.
    
    Uses dependency injection pattern compatible with FastAPI's get_db.
    """
    
    def __init__(self, db: Session):
        """
        Initialize repository with a database session.
        
        Args:
            db: SQLAlchemy Session (typically from Depends(get_db))
        """
        self.db = db
    
    def create_feedback(self, feedback_data: dict) -> Feedback:
        """
        Create a new feedback entry.
        
        Args:
            feedback_data: Dictionary with feedback fields
            
        Returns:
            Created Feedback object
            
        Raises:
            SQLAlchemyError: If database operation fails
        """
        feedback = Feedback(**feedback_data)
        self.db.add(feedback)
        self.db.flush()  # Get ID without committing (caller controls transaction)
        self.db.refresh(feedback)
        return feedback
    
    def get_user_feedback(
        self, 
        user_id: str, 
        limit: int = 20, 
        offset: int = 0
    ) -> List[Feedback]:
        """
        Get feedback for a specific user with pagination.
        
        Args:
            user_id: User ID to filter by
            limit: Maximum number of results (1-100)
            offset: Number of results to skip
            
        Returns:
            List of Feedback objects, ordered by created_at descending
        """
        # Enforce sensible limits
        limit = max(1, min(100, limit))
        offset = max(0, offset)
        
        return (
            self.db.query(Feedback)
            .filter(Feedback.user_id == user_id)
            .order_by(desc(Feedback.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )
    
    def get_all_feedback(
        self, 
        limit: int = 20, 
        offset: int = 0
    ) -> List[Feedback]:
        """
        Get all feedback (admin use only).
        
        Args:
            limit: Maximum number of results (1-100)
            offset: Number of results to skip
            
        Returns:
            List of Feedback objects, ordered by created_at descending
            
        Warning:
            This method returns feedback from ALL users. 
            Only call from admin-protected endpoints.
        """
        # Enforce sensible limits
        limit = max(1, min(100, limit))
        offset = max(0, offset)
        
        return (
            self.db.query(Feedback)
            .order_by(desc(Feedback.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )
    
    def count_user_feedback(self, user_id: str) -> int:
        """
        Count total feedback entries for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Total count of feedback entries
        """
        return self.db.query(Feedback).filter(Feedback.user_id == user_id).count()
    
    def count_all_feedback(self) -> int:
        """
        Count total feedback entries (admin use only).
        
        Returns:
            Total count of all feedback entries
        """
        return self.db.query(Feedback).count()
