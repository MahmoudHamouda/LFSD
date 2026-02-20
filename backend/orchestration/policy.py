import logging
from typing import Dict, Any

logger = logging.getLogger("orchestration.policy")

class ExecutionPolicy:
    """
    Execution Policy & Guardrails for deterministic tools.
    Defines what can auto-execute, rate limits, and confirmation rules.
    """
    
    # Define tool execution constraints
    RULES = {
        "MOBILITY": {
            "requires_confirmation": True,  # Cannot book automatically without explicit OK
            "rate_limit_per_minute": 5,
            "timeout_ms": 5000,
            "retries": 1
        },
        "FINANCE_READ": {
            "requires_confirmation": False,
            "rate_limit_per_minute": 20,
            "timeout_ms": 3000,
            "retries": 2
        }
    }

    @classmethod
    def can_auto_execute(cls, intent_name: str) -> bool:
        """Determines if a tool requires explicit user confirmation before modifying state."""
        rule = cls.RULES.get(intent_name, {})
        # Default to safe (requires confirmation) if unknown
        return not rule.get("requires_confirmation", True)
        
    @classmethod
    def get_timeout(cls, intent_name: str) -> int:
        return cls.RULES.get(intent_name, {}).get("timeout_ms", 5000)

    @classmethod
    def get_retries(cls, intent_name: str) -> int:
        return cls.RULES.get(intent_name, {}).get("retries", 0)

    @classmethod
    def enforce_rate_limit(cls, user_id: str, intent_name: str, cache_service=None) -> bool:
        """
        Check if the user has exceeded the tool-specific rate limit.
        (Implementation would normally use Redis via cache_service)
        """
        # Stub: Assume within limits
        return True
