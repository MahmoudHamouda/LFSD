import time
import uuid
import logging
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from .intent import IntentClassifier, Intent
from .router import ToolRouter
from .response import ResponseComposer
from models.logging_models import AuditLog
from models.models import ActivityFeed

logger = logging.getLogger("orchestration.master")

class Orchestrator:
    """
    Action Orchestration Layer (Tool-first, LLM-last).
    1) Classifies Intent
    2) Routes to deterministic Executor (fetching external data)
    3) Composes a response without LLM hallucination
    4) Logs to Audit and Activity feeds.
    """
    def __init__(self, db: Session, llm=None):
        self.db = db
        self.classifier = IntentClassifier()
        self.router = ToolRouter(db_session=self.db)
        self.composer = ResponseComposer(llm_service=llm)

    async def _log_audit(self, user_id: str, intent_name: str, executor_called: str, success: bool, latency_ms: float, error: str = None):
        """Write to structured Audit Log."""
        audit = AuditLog(
            id=str(uuid.uuid4()),
            actor_id=user_id,
            action="EXECUTOR_CALL",
            entity_type="ToolResult",
            entity_id=executor_called,
            changes_json={
                "intent": intent_name,
                "latency_ms": latency_ms,
                "success": success,
                "error": error
            }
        )
        self.db.add(audit)
        self.db.commit()

    async def _log_activity(self, user_id: str, title: str, description: str):
        """Write to Activity Feed (user-facing)."""
        feed = ActivityFeed(
            id=str(uuid.uuid4()),
            user_id=user_id,
            event_type="ORCHESTRATION_ACTION",
            description=description,
            metadata_json={"title": title}
        )
        self.db.add(feed)
        self.db.commit()

    async def process_message(self, text: str, user_id: str, context: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """
        Main entry point for tool-first orchestration.
        Returns (human_response, metrics_and_state)
        """
        start_time = time.time()
        
        # 1. Classify Intent
        intent = self.classifier.classify(text)
        
        # 2. Route to Executors (only if we have a matching deterministic tool)
        if intent.name in ["MOBILITY"]:
            # Valid action intent, run tool
            result = await self.router.execute_intent(intent, user_id, context)
            latency_ms = (time.time() - start_time) * 1000
            
            # Log Tool Call
            await self._log_audit(
                user_id=user_id,
                intent_name=intent.name,
                executor_called=intent.name,
                success=result.get("executor_found", False) and result.get("data") is not None,
                latency_ms=latency_ms,
                error=result.get("message") if not result.get("data") else None
            )
            
            # Only if executor supplied data, compose response
            if result.get("data"):
                human_answer = await self.composer.compose(intent.name, result["data"], context)
                
                # Report user-friendly activity log
                origin = result["data"].get("origin", "Location")
                destination = result["data"].get("destination", "Destination")
                await self._log_activity(user_id, "Route Computed", f"Found commute options from {origin} to {destination}")
                
                # Return the LLM-last, tool-first answer
                return human_answer, {
                    "is_orchestrator": True,
                    "intent": intent.name,
                    "options": result["data"]
                }
            else:
                # Ask clarifying question if tool required entities
                return result.get("message", "I need more information to complete that action."), {"is_orchestrator": True, "clarifying": True}
        
        # 3. Fallback to normal LLM conversation
        return None, {"is_orchestrator": False, "intent": "GENERAL"}
