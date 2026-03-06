import logging
import asyncio
from typing import Dict, Any, List
from .intent import Intent, IntentClassifier
from .policy import ExecutionPolicy
from .registry import IntegrationRegistry

logger = logging.getLogger("orchestration.router")

# ---------------------------------------------------------------------------
# Conversational clarification templates per intent
# ---------------------------------------------------------------------------
CLARIFICATION_PROMPTS = {
    "MOBILITY": {
        "missing_all": (
            "I'd love to help you get there! 🚗\n\n"
            "Could you tell me:\n"
            "1. **Where are you going?** (destination)\n"
            "2. **Where are you coming from?** (or I can use your current location)\n"
            "3. **When do you need to leave?** (now, or a specific time)"
        ),
        "missing_destination": (
            "Sure, I can help arrange a ride! "
            "**Where would you like to go?**"
        ),
        "missing_origin": (
            "Got it — heading to **{destination}**! "
            "**Where are you coming from?** (or say 'current location')"
        ),
    },
}


def _build_clarification(intent: Intent) -> str:
    """Build a friendly follow-up question when required entities are missing."""
    templates = CLARIFICATION_PROMPTS.get(intent.name, {})
    entities = intent.entities

    if intent.name == "MOBILITY":
        has_dest = "destination" in entities
        has_orig = "origin" in entities

        if not has_dest and not has_orig:
            return templates.get("missing_all", "Could you provide more details?")
        if not has_dest:
            return templates.get("missing_destination", "Where would you like to go?")
        if not has_orig:
            return templates.get("missing_origin", "Where are you coming from?").format(
                destination=entities.get("destination", "your destination")
            )

    return "Could you give me a bit more detail so I can help?"


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

        # 2. Check if required entities are present — ask conversational follow-up
        if not intent.required_entities_present:
            return {
                "executor_found": True, 
                "data": None, 
                "status": "clarify",
                "message": _build_clarification(intent)
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
                "error_type": "api_down",
                "message": (
                    "I'm sorry, the mobility service is temporarily unavailable. "
                    "Our team has been notified and is working on it. "
                    "Please try again in a few minutes."
                )
            }

        # 4. Call Executor with Timeout & Retries
        for attempt in range(retries + 1):
            try:
                # Wrap the executor call in a timeout
                result = await asyncio.wait_for(
                    executor.execute_safe(intent.entities, user_id, context),
                    timeout=timeout_sec
                )

                # Check if executor returned an error with a type
                if result.get("error"):
                    error_type = result.get("error_type", "unknown")
                    return {
                        "executor_found": True,
                        "data": result,
                        "status": "error",
                        "error_type": error_type,
                        "message": result.get("message", "Something went wrong.")
                    }

                return {
                    "executor_found": True,
                    "data": result,
                    "status": "success",
                    "message": "Structured data retrieved successfully."
                }
            except asyncio.TimeoutError:
                logger.warning(f"Executor {intent.name} timed out on attempt {attempt + 1}")
                if attempt == retries:
                    return {
                        "executor_found": True,
                        "data": None,
                        "status": "timeout",
                        "message": (
                            "The request is taking longer than expected. "
                            "This could be due to high demand. Please try again in a moment."
                        )
                    }
            except Exception as e:
                import uuid
                error_id = str(uuid.uuid4())[:12]
                logger.error(f"Executor {intent.name} failed [{error_id}]: {e}", exc_info=True)
                if attempt == retries:
                    return {
                        "executor_found": True, 
                        "data": None, 
                        "status": "error",
                        "message": (
                            "Something unexpected happened while processing your request. "
                            "Please try again shortly."
                        )
                    }
