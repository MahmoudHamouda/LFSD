import logging
import asyncio
from typing import Dict, Any, List
from .intent import Intent, IntentClassifier
from .policy import ExecutionPolicy
from .registry import IntegrationRegistry

logger = logging.getLogger("orchestration.router")

class ToolRouter:
    """
    Routes a classified Intent to the appropriate deterministic Tool/Executor.
    Fetches structured data before LLM generation.
    """
    def __init__(self, db_session=None):
        self.db_session = db_session

    async def execute_intent(self, intent: Intent, user_id: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Runs the executor for the given intent and returns structured data."""
        if context is None:
            context = {}
            
        # 1. Check if intent is recognized and has an executor in the registry
        executor = IntegrationRegistry.get_executor(intent.name)
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

        # 3. Initialize the Executor lazily
        logger.info(f"Routing to {intent.name} executor with entities {intent.entities}")
        setup_success = await executor.setup()
        if not setup_success or not getattr(executor, 'is_healthy', True):
            # Graceful degradation if API down
            import uuid
            error_id = str(uuid.uuid4())[:12]
            raw_error = getattr(executor, 'error_msg', "Service is currently offline.")
            logger.error(f"Executor {intent.name} setup failed [{error_id}]: {raw_error}")
            return {
                "executor_found": True, 
                "data": None, 
                "status": "offline", 
                "message": f"This service is currently unavailable. Please contact support with Error ID: {error_id}"
            }

        # 4. Call Executor with Timeout & Retries
        for attempt in range(retries + 1):
            try:
                # Wrap the executor call in a timeout
                result = await asyncio.wait_for(
                    executor.execute_safe(intent.entities, user_id, context),
                    timeout=timeout_sec
                )
                return {
                    "executor_found": True,
                    "data": result,
                    "status": "success",
                    "message": "Structured data retrieved successfully."
                }
            except asyncio.TimeoutError:
                logger.warning(f"Executor {intent.name} timed out on attempt {attempt + 1}")
                if attempt == retries:
                    return {"executor_found": True, "data": None, "message": "Service timed out."}
            except Exception as e:
                import uuid
                error_id = str(uuid.uuid4())[:12]
                logger.error(f"Executor {intent.name} failed [{error_id}]: {e}", exc_info=True)
                if attempt == retries:
                    return {
                        "executor_found": True, 
                        "data": None, 
                        "message": f"Execution failed. Please contact support with Error ID: {error_id}"
                    }
