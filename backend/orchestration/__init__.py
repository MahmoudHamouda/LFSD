from .registry import IntegrationRegistry

# Discover deployed executors
try:
    import backend.mobility.executor
except ImportError:
    pass
