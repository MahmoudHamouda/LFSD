"""
Fair-lending controls: adverse-action reasons + disparate-impact testing.

Bridge #2, part 3 — the two gaps the inclusion-readiness scorecard flags as
zero (``bias_testing``, ``adverse_action``). Both are deterministic and pair
directly with the AssessmentEngine:

  * ``AdverseActionReasoner`` turns an ``AssessmentResult`` into specific,
    accurate reason statements (ECOA/FCRA require the *actual* factors, not
    boilerplate) — it simply reads the lowest-scoring rules, which already
    carry human-readable ``reasoning`` and a ``regulatory_ref``.
  * ``four_fifths_check`` implements the EEOC/DOJ "four-fifths rule" for
    disparate impact across groups — a standard first-line fairness monitor.

Nothing here makes a lending decision; it makes decisions *explainable and
testable*, which is what a regulated institution must be able to show.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from ..scoring.schema import AssessmentResult


@dataclass
class AdverseActionReason:
    code: str  # the rule id — stable, mappable to the institution's reason codes
    statement: str  # customer-facing explanation
    regulatory_ref: Optional[str] = None


class AdverseActionReasoner:
    """Derives specific adverse-action reasons from an assessment result."""

    def __init__(self, max_reasons: int = 4, threshold: float = 50.0):
        # ECOA guidance: disclose the principal reasons (commonly up to 4).
        self.max_reasons = max_reasons
        self.threshold = threshold

    def reasons(self, result: AssessmentResult) -> List[AdverseActionReason]:
        """Lowest-scoring rules below threshold, worst first, capped."""
        rules = [
            r
            for d in result.dimension_results
            for r in d.rule_results
            if r.score < self.threshold and not r.missing_input
        ]
        rules.sort(key=lambda r: r.score)
        return [
            AdverseActionReason(
                code=r.rule_id,
                statement=r.reasoning,
                regulatory_ref=r.regulatory_ref,
            )
            for r in rules[: self.max_reasons]
        ]


@dataclass
class DisparateImpactResult:
    reference_group: str
    rates: Dict[str, float]
    ratios: Dict[str, float]  # group_rate / reference_rate
    passes: bool  # True if all ratios >= 0.8 (four-fifths rule)
    flagged_groups: List[str]


def four_fifths_check(
    approvals: Dict[str, int], totals: Dict[str, int]
) -> DisparateImpactResult:
    """
    Four-fifths rule across groups.

    ``approvals``/``totals`` are counts keyed by group label (e.g. protected
    class). The group with the highest selection (approval) rate is the
    reference; any group whose rate is < 80% of the reference rate is flagged
    for disparate-impact review. This is a monitoring signal, not a verdict.
    """
    rates = {
        g: (approvals.get(g, 0) / totals[g]) if totals.get(g) else 0.0 for g in totals
    }
    if not rates or max(rates.values()) == 0:
        return DisparateImpactResult("", rates, {}, True, [])

    reference_group = max(rates, key=rates.get)
    ref_rate = rates[reference_group]
    ratios = {g: (rate / ref_rate if ref_rate else 0.0) for g, rate in rates.items()}
    flagged = [g for g, ratio in ratios.items() if ratio < 0.8]
    return DisparateImpactResult(
        reference_group=reference_group,
        rates=rates,
        ratios=ratios,
        passes=not flagged,
        flagged_groups=flagged,
    )
