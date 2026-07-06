"""
Runnable demo: one engine, two very different scorecards.

    python -m responsible_ai.scoring.demo

Shows the same AssessmentEngine producing (1) a consumer Viv wellbeing score and
(2) an institutional inclusion-readiness scorecard — purely by swapping config.
"""

from __future__ import annotations

from .engine import AssessmentEngine
from .configs.viv_wellbeing import VIV_WELLBEING_CONFIG
from .configs.inclusion_readiness import INCLUSION_READINESS_CONFIG


def _demo_viv() -> None:
    inputs = {
        "savings_rate": 0.12,
        "emergency_fund_months": 2.0,
        "debt_to_income": 0.28,
        "invested_ratio": 0.15,
        "weekly_active_minutes": 120,
        "avg_sleep_hours": 6.5,
        "focus_ratio": 0.45,
    }
    result = AssessmentEngine(VIV_WELLBEING_CONFIG).evaluate(inputs)
    print("=" * 70)
    print("CONSUMER: Viv wellbeing score")
    print("=" * 70)
    print(result.explain())


def _demo_readiness() -> None:
    # A small credit union part-way through adoption.
    answers = {
        "data_quality_documented": 1.0,
        "permissible_data_confirmed": 0.5,
        "model_governance_process": 0.5,
        "decision_audit_trail": 1.0,  # provided by this framework
        "human_in_the_loop": 0.5,
        "disparate_impact_testing": 0.0,  # gap
        "adverse_action_reasons": 0.0,  # gap
        "consent_captured_and_stored": 0.5,
        "pii_minimized_to_ai": 1.0,  # provided by this framework
        "explanations_traceable": 1.0,  # provided by this framework
        "measurement_plan_defined": 0.5,
    }
    result = AssessmentEngine(INCLUSION_READINESS_CONFIG).evaluate(answers)
    print("\n" + "=" * 70)
    print("INSTITUTION: inclusion-readiness scorecard")
    print("=" * 70)
    print(result.explain())
    gaps = [
        r.rule_id
        for d in result.dimension_results
        for r in d.rule_results
        if r.score < 50
    ]
    print(f"\nTop gaps to close before pilot: {gaps}")


def _demo_families() -> None:
    """The same engine scores readiness for each of the 10 use-case families."""
    from .configs import FAMILY_CONFIGS
    from .engine import AssessmentEngine as _E

    print("\n" + "=" * 70)
    print("PER-FAMILY readiness (partial-adoption baseline of 0.5 everywhere)")
    print("=" * 70)
    for slug, config in FAMILY_CONFIGS.items():
        answers = {r.metric: 0.5 for r in config.rules}
        result = _E(config).evaluate(answers)
        print(f"  {slug:22} {result.composite_score:5.1f}/100  — {config.name}")


if __name__ == "__main__":
    _demo_viv()
    _demo_readiness()
    _demo_families()
