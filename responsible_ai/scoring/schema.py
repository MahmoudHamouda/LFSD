"""
Config-driven, deterministic, explainable scoring — schema.

This is the generalized form of HELM's original ``score_engine.py`` pattern:
declarative, versioned policies whose every output traces back to a named rule
and the input that triggered it. Nothing here calls an LLM.

An institution adopting this framework supplies its *own* ``AssessmentConfig``
(dimensions + rules). The engine (see ``engine.py``) is identical regardless of
config — the same code produces HELM's consumer "Viv" wellbeing score and a
bank's "inclusion readiness" scorecard. That is the whole point: the scoring is
a reusable method, not a hard-coded product.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


# ---------------------------------------------------------------------------
# Rule bands — the declarative, no-code way to score a metric
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Band:
    """
    A single threshold band mapping an input metric to a 0-100 sub-score.

    A rule is scored by finding the first band (evaluated top to bottom) whose
    ``max_value`` the metric is <=. This keeps scoring declarative and auditable:
    an institution can read the config and know exactly why a value scored what
    it did, and the ``reasoning`` string is surfaced verbatim in the result.

    Example (lower is worse, e.g. months of emergency buffer):
        Band(max_value=1,   score=20, reasoning="< 1 month of buffer — high risk")
        Band(max_value=3,   score=60, reasoning="1-3 months of buffer — fragile")
        Band(max_value=None, score=100, reasoning=">= 3 months of buffer — resilient")
    """

    score: float  # 0-100 sub-score awarded when the metric falls in this band
    reasoning: str  # human-readable explanation, surfaced to the user/auditor
    # Upper bound of this band (inclusive). None means "no upper bound" (catch-all).
    max_value: Optional[float] = None


@dataclass
class Rule:
    """
    One scored factor within a dimension.

    A rule reads a single ``metric`` key from the assessment inputs and maps it
    to a 0-100 score via ``bands`` (declarative) or ``scorer`` (a callable, for
    the rare cases bands can't express). Every rule carries an id, description,
    and weight so the composite is transparent and reproducible.
    """

    id: str
    dimension: str
    metric: str  # key read from the inputs dict
    description: str
    weight: float = 1.0  # relative weight of this rule within its dimension
    bands: List[Band] = field(default_factory=list)

    # Optional escape hatch: (metric_value, inputs) -> (score, reasoning).
    # Prefer bands; use this only when a rule genuinely needs custom logic.
    scorer: Optional[Callable[[float, Dict], tuple]] = field(default=None, repr=False)

    # Governance metadata (mirrors the original ScoringPolicy governance fields).
    owner: str = "platform"
    regulatory_ref: Optional[str] = None  # e.g. "ECOA/Reg B", "FCRA §615"


@dataclass
class Dimension:
    """A weighted group of rules (e.g. 'Wealth', or 'Fair-lending controls')."""

    name: str
    weight: float = 1.0  # relative weight of this dimension in the composite
    description: str = ""


@dataclass
class AssessmentConfig:
    """
    A complete, versioned scoring specification.

    This is the unit an institution owns and edits. It is data, not code — which
    is what makes the engine reusable and what makes every score defensible in an
    audit: the config *is* the policy.
    """

    name: str
    version: str
    dimensions: List[Dimension]
    rules: List[Rule]
    description: str = ""
    owner: str = "platform"
    # Free-text notes on what changed between versions (model-risk / governance).
    changelog: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Results — fully traceable output
# ---------------------------------------------------------------------------


@dataclass
class RuleResult:
    """The outcome of one rule — the atomic unit of explainability."""

    rule_id: str
    dimension: str
    metric: str
    metric_value: Optional[float]
    score: float  # 0-100
    weight: float
    reasoning: str
    regulatory_ref: Optional[str] = None
    missing_input: bool = False


@dataclass
class DimensionResult:
    """Weighted roll-up of a dimension's rule results."""

    name: str
    score: float  # 0-100
    weight: float
    rule_results: List[RuleResult]


@dataclass
class AssessmentResult:
    """
    The full, explainable output of an assessment run.

    ``composite_score`` is the headline number; ``dimension_results`` and their
    ``rule_results`` are the audit trail behind it. ``explain()`` renders a plain
    -language rationale — the "traces back to explicit criteria" requirement.
    """

    config_name: str
    config_version: str
    composite_score: float  # 0-100
    dimension_results: List[DimensionResult]
    missing_inputs: List[str] = field(default_factory=list)

    def explain(self) -> str:
        """Human-readable rationale for the composite score."""
        lines = [
            f"{self.config_name} v{self.config_version} — "
            f"composite score {self.composite_score:.1f}/100",
        ]
        for dim in self.dimension_results:
            lines.append(f"\n▸ {dim.name}: {dim.score:.1f}/100 (weight {dim.weight})")
            for r in dim.rule_results:
                flag = " [missing input]" if r.missing_input else ""
                ref = f" ({r.regulatory_ref})" if r.regulatory_ref else ""
                lines.append(
                    f"    - {r.rule_id}: {r.score:.0f}/100 — {r.reasoning}{ref}{flag}"
                )
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        """Serializable form for APIs, storage, and audit records."""
        return {
            "config": {"name": self.config_name, "version": self.config_version},
            "composite_score": round(self.composite_score, 2),
            "dimensions": [
                {
                    "name": d.name,
                    "score": round(d.score, 2),
                    "weight": d.weight,
                    "rules": [
                        {
                            "rule_id": r.rule_id,
                            "metric": r.metric,
                            "metric_value": r.metric_value,
                            "score": round(r.score, 2),
                            "weight": r.weight,
                            "reasoning": r.reasoning,
                            "regulatory_ref": r.regulatory_ref,
                            "missing_input": r.missing_input,
                        }
                        for r in d.rule_results
                    ],
                }
                for d in self.dimension_results
            ],
            "missing_inputs": self.missing_inputs,
        }
