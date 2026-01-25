"""
Productivity Services Package

This package manages services related to time management (Calendars) and 
geographic intelligence (Maps). 

The package is partitioned into:
1. Calendar Services: Unified interface for scheduling (Google, Outlook).
2. Mapping Services: Geographic and distance calculations.
"""

from typing import Dict, Type, Optional, List, Any
from datetime import datetime
from .base_calendar_service import BaseCalendarService

# Define Public API
__all__ = [
    "get_calendar_service",
    "get_mapping_service",
    "get_productivity_aggregator",
    "BaseCalendarService",
    "ProductivityAggregator",
    "CALENDAR_PROVIDERS",
    "MAPPING_PROVIDERS"
]

# Capability Registry
CALENDAR_PROVIDERS = {
    "google_calendar": {
        "class_path": "google_calendar_service.GoogleCalendarService",
        "capabilities": ["read", "write", "availability", "recurring"],
        "auth_type": "oauth2"
    },
    "outlook_calendar": {
        "class_path": "outlook_calendar_service.OutlookCalendarService",
        "capabilities": ["read", "write", "availability"],
        "auth_type": "oauth2"
    }
}

MAPPING_PROVIDERS = {
    "google_maps": {
        "class_path": "google_maps_service.GoogleMapsService",
        "capabilities": ["geocode", "distance_matrix", "reverse_geocode"]
    }
}

# Lazy Loading Registry
_services_cache: Dict[str, Any] = {}

def get_calendar_service(provider: str, **kwargs) -> BaseCalendarService:
    """
    Factory to resolve and instantiate a calendar service by provider key.
    
    Args:
        provider: Identifier (e.g., 'google_calendar').
        **kwargs: Arguments for service initialization (e.g. access_token).
    """
    if provider not in CALENDAR_PROVIDERS:
        raise ValueError(f"Unsupported calendar provider: {provider}")
    
    # Lazy import to prevent circular dependencies and side effects on package import
    import importlib
    
    config = CALENDAR_PROVIDERS[provider]
    module_name, class_name = config["class_path"].rsplit(".", 1)
    
    try:
        module = importlib.import_module(f".{module_name}", package=__name__)
        service_class = getattr(module, class_name)
        
        # Instantiate fresh to avoid stale config/token issues in long-running processes
        service = service_class(**kwargs)
        
        # Runtime validation against base class
        if not isinstance(service, BaseCalendarService):
            raise TypeError(f"Provider {provider} does not conform to BaseCalendarService")
            
        return service
        
    except (ImportError, AttributeError) as e:
        raise RuntimeError(f"Failed to load calendar provider {provider}: {e}")

def get_mapping_service(provider: str = "google_maps") -> Any:
    """
    Factory to resolve mapping services.
    """
    if provider not in MAPPING_PROVIDERS:
        raise ValueError(f"Unsupported mapping provider: {provider}")
        
    import importlib
    config = MAPPING_PROVIDERS[provider]
    module_name, class_name = config["class_path"].rsplit(".", 1)
    
    # Mapping services are often stateless and can be cached as singletons safely if designed well,
    # but to be safe and match user feedback on singletons, we can provide fresh or cached instances.
    # For now, following 'get_client' pattern in GoogleMapsService which manages internal state.
    
    try:
        module = importlib.import_module(f".{module_name}", package=__name__)
        service_class = getattr(module, class_name)
        return service_class()
    except (ImportError, AttributeError) as e:
        raise RuntimeError(f"Failed to load mapping provider {provider}: {e}")

class ProductivityAggregator:
    """
    Aggregator for concurrent productivity service operations.
    Follows the same concurrency and resilience patterns as MobilityAggregator.
    """
    
    async def get_all_events(
        self, 
        user_id: str, 
        time_min: datetime, 
        time_max: datetime,
        provider_data: Dict[str, Dict[str, Any]] # {provider_key: {kwargs}}
    ) -> List[Any]:
        """
        Fetch events from multiple calendar providers concurrently.
        """
        import asyncio
        tasks = []
        
        for provider, kwargs in provider_data.items():
            if provider in CALENDAR_PROVIDERS:
                service = get_calendar_service(provider, **kwargs)
                tasks.append(self._safe_fetch(provider, service, user_id, time_min, time_max))
        
        results = await asyncio.gather(*tasks)
        
        # Flatten results
        all_events = []
        for provider_name, events in results:
            all_events.extend(events)
            
        return all_events

    async def _safe_fetch(self, name, service, *args) -> tuple:
        try:
            res = await asyncio.wait_for(service.list_events(*args), timeout=10.0)
            return (name, res)
        except Exception as e:
            # Import logger here or globally
            import logging
            logging.getLogger(__name__).error(f"Productivity aggregator failed for {name}: {e}")
            return (name, [])

def get_productivity_aggregator() -> ProductivityAggregator:
    return ProductivityAggregator()
