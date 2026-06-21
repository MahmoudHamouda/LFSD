"""
Mobility Services Package

Integrates with mobility providers (Uber, RTA) and provides a unified
interface for price comparison and idempotent booking via a central Aggregator.
"""

import importlib
from typing import Dict, Any, Type, Optional

from .base_mobility_service import BaseMobilityService
from .mobility_aggregator import MobilityAggregator, get_mobility_aggregator

# Provider Capabilities Registry
MOBILITY_PROVIDERS = {
    "uber": {
        "class_path": "uber_service.UberService",
        "capabilities": ["on_demand", "ride_share"],
        "supports_booking": True,
    },
    "rta": {
        "class_path": "rta_service.RTAService",
        "capabilities": ["public_transit", "metro", "bus", "sched_routes"],
        "supports_booking": True,
    },
}

__all__ = [
    "get_mobility_aggregator",
    "get_mobility_provider",
    "BaseMobilityService",
    "MOBILITY_PROVIDERS",
]


def get_mobility_provider(provider_key: str) -> BaseMobilityService:
    """
    Factory to resolve and instantiate a specific mobility provider.

    Args:
        provider_key: Identifier (e.g., 'uber', 'rta')

    Returns:
        An instance of the requested provider service.
    """
    pkg_key = provider_key.lower()
    if pkg_key not in MOBILITY_PROVIDERS:
        raise ValueError(f"Unsupported mobility provider: {provider_key}")

    config = MOBILITY_PROVIDERS[pkg_key]
    module_name, class_name = config["class_path"].rsplit(".", 1)

    try:
        # Lazy import to manage memory and avoid circularities
        module = importlib.import_module(f".{module_name}", package=__name__)
        service_class = getattr(module, class_name)
        return service_class()
    except (ImportError, AttributeError) as e:
        raise RuntimeError(f"Failed to load mobility provider {provider_key}: {e}")
