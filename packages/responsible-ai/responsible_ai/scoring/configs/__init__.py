"""Reference and example assessment configurations.

- ``VIV_WELLBEING_CONFIG``       — consumer wellbeing (the HELM/Viv score as config).
- ``INCLUSION_READINESS_CONFIG`` — cross-cutting institutional readiness.
- ``FAMILY_CONFIGS``             — per-use-case readiness scorecards (10 families).
"""

from .families import FAMILY_CONFIGS
from .inclusion_readiness import INCLUSION_READINESS_CONFIG
from .viv_wellbeing import VIV_WELLBEING_CONFIG

__all__ = [
    "VIV_WELLBEING_CONFIG",
    "INCLUSION_READINESS_CONFIG",
    "FAMILY_CONFIGS",
]
