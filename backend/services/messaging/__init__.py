"""
Messaging Services Package

Centralizes communications (WhatsApp, SMS, etc).
Provides factory methods for resolving providers and a centralized
orchestration layer for outbound messaging.
"""

from typing import Dict, Any, Optional
import importlib

from .base_messaging_service import BaseMessagingService, MessageResponse

# Provider Registry with lazy-loading configuration
MESSAGING_PROVIDERS = {
    "whatsapp": {
        "class_path": "whatsapp_service.WhatsAppService",
        "capabilities": ["text", "template", "webhooks"],
    }
}

__all__ = [
    "get_messaging_provider",
    "BaseMessagingService",
    "MessageResponse",
    "MESSAGING_PROVIDERS"
]

# Singleton cache for long-running processes
_service_cache: Dict[str, BaseMessagingService] = {}

def get_messaging_provider(provider_key: str, use_cache: bool = True) -> BaseMessagingService:
    """
    Factory to resolve and instantiate messaging providers.
    
    Args:
        provider_key: Identifier (e.g. 'whatsapp')
        use_cache: If True, returns a singleton instance.
    """
    key = provider_key.lower()
    
    if use_cache and key in _service_cache:
        return _service_cache[key]

    if key not in MESSAGING_PROVIDERS:
        raise ValueError(f"Unsupported messaging provider: {provider_key}")

    config = MESSAGING_PROVIDERS[key]
    module_name, class_name = config["class_path"].rsplit(".", 1)

    try:
        # Dynamic import to minimize startup overhead and circular dependencies
        module = importlib.import_module(f".{module_name}", package=__name__)
        service_class = getattr(module, class_name)
        instance = service_class()
        
        if use_cache:
            _service_cache[key] = instance
            
        return instance
    except (ImportError, AttributeError) as e:
        raise RuntimeError(f"Failed to load messaging provider {provider_key}: {e}")
