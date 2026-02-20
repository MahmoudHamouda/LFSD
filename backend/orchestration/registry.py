import logging
from typing import Dict, Any, Type, Optional
from backend.orchestration.base_executor import BaseExecutor

logger = logging.getLogger("orchestration.registry")

class IntegrationRegistry:
    """
    Central registry for all Action Orchestrator tools (Lifestyle, Wealth, Health, etc).
    Dynamically discovers and registers tools without causing hard-crashes if an import
    or initialization fails.
    """
    _executors: Dict[str, Type[BaseExecutor]] = {}

    @classmethod
    def register(cls, intent_name: str):
        """
        Decorator to register a BaseExecutor class to a specific Intent.
        Example:
            @IntegrationRegistry.register("MOBILITY")
            class MobilityExecutor(BaseExecutor):
                ...
        """
        def wrapper(executor_cls: Type[BaseExecutor]):
            cls._executors[intent_name] = executor_cls
            logger.info(f"Registered Executor: {executor_cls.__name__} for Intent: {intent_name}")
            return executor_cls
        return wrapper

    @classmethod
    def get_executor(cls, intent_name: str) -> Optional[BaseExecutor]:
        """
        Returns a newly instantiated Executor for the given intent, if registered.
        Lazy instantiation guarantees that if an Executor fails to instantiate due to
        API key errors, it happens at request time, not server boot, allowing graceful degradation.
        """
        executor_cls = cls._executors.get(intent_name)
        if not executor_cls:
            return None
            
        try:
             return executor_cls()
        except Exception as e:
             logger.error(f"Failed to instantiate executor for {intent_name}: {e}", exc_info=True)
             # Return a degraded executor that immediately fails safe
             return DegradedExecutor(error_msg=str(e))


class DegradedExecutor(BaseExecutor):
     """A stub executor returned when the requested integration fails to initialize."""
     def __init__(self, error_msg: str):
          super().__init__()
          self.error_msg = error_msg
          self.is_healthy = False
          
     async def setup(self) -> bool:
          return False
          
     async def execute_safe(self, entities: Dict[str, Any], user_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
          return {"status": "error", "error_message": f"Integration offline: {self.error_msg}"}
