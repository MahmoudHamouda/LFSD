from typing import Optional, Dict, Any
from loguru import logger
from sqlalchemy.orm import Session
from models.database import SessionLocal
from models.logging_models import AuditLog, ActivityFeed, Notification
from datetime import datetime
import uuid
import threading # For firing async tasks if needed, or just run sync for now

import functools
import inspect

class GA4Events:
    USER_LOGIN = "user_login"
    GOAL_CREATED = "goal_created"
    TRANSACTION_VIEWED = "transaction_viewed"
    ERROR_OCCURRED = "error_occurred"

class Observability:
    """
    Central observability entry point.
    Handles Logging (via loguru), Audit, Activity Feed, Notifications, and Analytics.
    """
    
    @staticmethod
    def audit_action(action: str, entity_type: str):
        """
        Decorator to automatically audit log a function call.
        Requires the function to have 'user_id' and return an object with 'id' available,
        or explicitly pass entity_id in kwargs. 
        """
        def decorator(func):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                # Execute
                result = await func(*args, **kwargs)
                
                # Extract Info (Best Effort)
                try:
                    user_id = kwargs.get("user_id")
                    # Try to find entity_id from result or kwargs
                    entity_id = kwargs.get("entity_id") or getattr(result, "id", "unknown")
                    
                    if user_id:
                        Observability.track_action(
                            actor_id=str(user_id),
                            action=action,
                            entity_type=entity_type,
                            entity_id=str(entity_id),
                            actor_type="user"
                        )
                except Exception as e:
                    logger.warning(f"Auto-audit failed: {e}")
                
                return result
            return wrapper
        return decorator

    @staticmethod
    def track_ga_event(event_name: str, params: Dict[str, Any], user_id: Optional[str] = None):
        """
        Sends event to Google Analytics 4.
        """
        # TODO: Implement actual HTTP call to GA4 Measurement Protocol
        # For now, just structured log it
        logger.info(
            f"GA4 EVENT: {event_name}",
            extra={
                "event_type": "ga4_event",
                "ga4_name": event_name,
                "ga4_params": params,
                "user_id": user_id
            }
        )

    @staticmethod
    def _safe_commit(session: Session, obj):
        try:
            session.add(obj)
            session.commit()
            session.refresh(obj)
        except Exception as e:
            logger.error(f"OBSERVABILITY DB ERROR: {e}")
            session.rollback()

    @staticmethod
    def track_action(
        actor_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        changes: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        actor_type: str = "user"
    ):
        """
        Records a business action.
        ALWAYS writes to AuditLog.
        """
        if not correlation_id:
            logger.warning("No correlation_id provided for track_action.")
            correlation_id = str(uuid.uuid4())

        # 1. Structure Log (stdout -> Cloud Logging)
        logger.info(
            f"ACTION: {action} on {entity_type}:{entity_id}",
            extra={
                "event_type": "audit_log",
                "actor_id": actor_id,
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "correlation_id": correlation_id
            }
        )

        # 2. Persist to DB (AuditLog)
        with SessionLocal() as db:
            audit = AuditLog(
                actor_id=actor_id,
                actor_type=actor_type,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                changes_json=changes,
                correlation_id=correlation_id,
                timestamp=datetime.utcnow()
            )
            Observability._safe_commit(db, audit)

    @staticmethod
    def emit_activity(
        user_id: str,
        title: str,
        description: str,
        event_type: str,
        icon: str = "default",
        action_link: Optional[str] = None,
        correlation_id: Optional[str] = None
    ):
        """
        Adds an item to the user's Activity Feed.
        """
        logger.info(
            f"ACTIVITY: {title}",
            extra={
                "event_type": "activity_feed",
                "user_id": user_id,
                "title": title,
                "correlation_id": correlation_id
            }
        )

        with SessionLocal() as db:
            activity = ActivityFeed(
                user_id=user_id,
                event_type=event_type,
                title=title,
                description=description,
                icon=icon,
                action_link=action_link,
                correlation_id=correlation_id,
                created_at=datetime.utcnow()
            )
            Observability._safe_commit(db, activity)

    @staticmethod
    def send_notification(
        user_id: str,
        subject: str,
        body: str,
        channel: str = "in_app",
        priority: str = "normal",
        payload: Optional[Dict[str, Any]] = None
    ):
        """
        Queues a notification.
        """
        logger.info(
            f"NOTIFICATION: {subject} -> {user_id}",
            extra={
                "event_type": "notification",
                "user_id": user_id,
                "channel": channel
            }
        )

        with SessionLocal() as db:
            note = Notification(
                user_id=user_id,
                channel=channel,
                status="pending",
                priority=priority,
                subject=subject,
                body=body,
                payload_json=payload,
                created_at=datetime.utcnow()
            )
            Observability._safe_commit(db, note)
            # In a real system, we'd fire a celery task or similar here to process sends.
