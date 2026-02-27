from .registry import IntegrationRegistry

# Discover deployed executors
try:
    import mobility.executor
except ImportError:
    pass
