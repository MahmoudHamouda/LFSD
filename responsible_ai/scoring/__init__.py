"""Config-driven, deterministic, explainable scoring."""

from .engine import AssessmentEngine, evaluate
from .schema import (
    AssessmentConfig,
    AssessmentResult,
    Band,
    Dimension,
    DimensionResult,
    Rule,
    RuleResult,
)

__all__ = [
    "AssessmentEngine",
    "evaluate",
    "AssessmentConfig",
    "AssessmentResult",
    "Band",
    "Dimension",
    "DimensionResult",
    "Rule",
    "RuleResult",
]
