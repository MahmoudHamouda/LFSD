import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple

logger = logging.getLogger("orchestration.base_executor")


class BaseExecutor(ABC):
    """
    Abstract base class for all Action Provider Integrations.
    Enforces a safe execution lifecycle: setup() -> execute_safe()
    to prevent unhandled third-party API exceptions from crashing the Orchestrator.
    """

    def __init__(self):
        self.is_healthy = True

    async def setup(self) -> bool:
        """
        Lazy Initialization hook.
        Override to load API keys, connect clients, or test health.
        If it returns False or throws, the tool is marked offline gracefully.
        """
        return True

    @abstractmethod
    async def execute_safe(
        self, entities: Dict[str, Any], user_id: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        The core logic of the tool. Must return a structured dictionary.
        Do NOT wrap in try/except here; the Orchestrator Router will catch and wrap it.
        Return format must include:
        {
           "status": "success" | "error" | "clarify",
           ...data
        }
        """
        pass
