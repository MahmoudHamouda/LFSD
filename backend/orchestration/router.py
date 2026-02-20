import logging
import asyncio
from typing import Dict, Any, List
from .intent import Intent, IntentClassifier
from mobility.executor import MobilityExecutor
from .policy import ExecutionPolicy

logger = logging.getLogger("orchestration.router")

class ToolRouter:
    """
    Routes a classified Intent to the appropriate deterministic Tool/Executor.
    Fetches structured data before LLM generation.
    """
    def __init__(self, db_session=None):
        self.db_session = db_session
        self.executors = {
            "MOBILITY": MobilityExecutor(),
            # "FINANCE": FinanceExecutor(),
            # "HEALTH": HealthExecutor()
        }

    async def execute_intent(self, intent: Intent, user_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Runs the executor for the given intent and returns structured data."""
        if context is None:
            context = {}
            
        # 1. Check if intent is recognized and has an executor
        executor = self.executors.get(intent.name)
        if not executor:
            return {"executor_found": False, "data": None, "message": "No specific tool mapped for this intent."}

        # 2. Check if required entities are present
        if not intent.required_entities_present:
            return {
                "executor_found": True, 
                "data": None, 
                "message": f"Missing required information for {intent.name}. Please clarify."
            }

        # Enforce rate limits based on Policy
        if not ExecutionPolicy.enforce_rate_limit(user_id, intent.name):
            return {"executor_found": True, "data": None, "message": "Too many requests. Please slow down."}

        timeout_sec = ExecutionPolicy.get_timeout(intent.name) / 1000.0
        retries = ExecutionPolicy.get_retries(intent.name)

        # 3. Call Executor with Timeout & Retries
        logger.info(f"Routing to {intent.name} executor with entities {intent.entities}")
        for attempt in range(retries + 1):
            try:
                # Wrap the executor call in a timeout
                result = await asyncio.wait_for(
                    executor.execute(intent.entities, user_id, context),
                    timeout=timeout_sec
                )
                return {
                    "executor_found": True,
                    "data": result,
                    "message": "Structured data retrieved successfully."
                }
            except asyncio.TimeoutError:
                logger.warning(f"Executor {intent.name} timed out on attempt {attempt + 1}")
                if attempt == retries:
                    return {"executor_found": True, "data": None, "message": "Service timed out."}
            except Exception as e:
                logger.error(f"Executor {intent.name} failed: {e}", exc_info=True)
                if attempt == retries:
                    return {"executor_found": True, "data": None, "message": f"Execution failed: {str(e)}"}
