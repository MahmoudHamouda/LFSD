"""
Tests for the Responsible-AI framework. Self-contained so they travel with the
package when an institution lifts it.

    python -m pytest responsible_ai/tests -q
"""

from responsible_ai.scoring import (
    AssessmentConfig,
    AssessmentEngine,
    Band,
    Dimension,
    Rule,
)
from responsible_ai.scoring.configs import (
    FAMILY_CONFIGS,
    INCLUSION_READINESS_CONFIG,
    VIV_WELLBEING_CONFIG,
)
from responsible_ai.governance import (
    AdverseActionReasoner,
    ConsentRecord,
    ConsentService,
    InMemoryConsentStore,
    PIIRedactor,
    four_fifths_check,
)


# -- engine determinism & traceability -------------------------------------


def test_engine_is_deterministic():
    inputs = {
        "savings_rate": 0.12,
        "emergency_fund_months": 2.0,
        "debt_to_income": 0.28,
    }
    e = AssessmentEngine(VIV_WELLBEING_CONFIG)
    assert e.evaluate(inputs).composite_score == e.evaluate(inputs).composite_score


def test_every_score_has_reasoning():
    result = AssessmentEngine(INCLUSION_READINESS_CONFIG).evaluate(
        {r.metric: 1.0 for r in INCLUSION_READINESS_CONFIG.rules}
    )
    for dim in result.dimension_results:
        for rr in dim.rule_results:
            assert rr.reasoning  # no silent, unexplained scores


def test_missing_input_scores_zero_and_is_flagged():
    result = AssessmentEngine(VIV_WELLBEING_CONFIG).evaluate({})  # nothing provided
    assert result.missing_inputs
    for dim in result.dimension_results:
        for rr in dim.rule_results:
            assert rr.missing_input and rr.score == 0.0


def test_bands_map_metric_to_expected_score():
    cfg = AssessmentConfig(
        name="t",
        version="1",
        dimensions=[Dimension(name="D")],
        rules=[
            Rule(
                id="r",
                dimension="D",
                metric="m",
                description="",
                bands=[
                    Band(max_value=1, score=20, reasoning="low"),
                    Band(max_value=None, score=100, reasoning="high"),
                ],
            )
        ],
    )
    assert AssessmentEngine(cfg).evaluate({"m": 0.5}).composite_score == 20
    assert AssessmentEngine(cfg).evaluate({"m": 5}).composite_score == 100


def test_orphan_rule_config_rejected():
    cfg = AssessmentConfig(
        name="bad",
        version="1",
        dimensions=[Dimension(name="D")],
        rules=[Rule(id="r", dimension="OTHER", metric="m", description="")],
    )
    try:
        AssessmentEngine(cfg)
        assert False, "expected ValueError for orphaned rule"
    except ValueError:
        pass


# -- governance ------------------------------------------------------------


def test_pii_redaction_and_minimization():
    rep = PIIRedactor().redact_text("a@b.com 555-123-4567 123-45-6789")
    assert "[EMAIL_REDACTED]" in rep.text and "[SSN_REDACTED]" in rep.text
    assert PIIRedactor().minimize_context(
        {"savings_rate": 0.1, "name": "x"}, allow=["savings_rate"]
    ) == {"savings_rate": 0.1}


def test_consent_default_deny_and_latest_wins():
    svc = ConsentService(InMemoryConsentStore())
    assert svc.has_consent("u", "p") is False
    svc.record(ConsentRecord("u", "p", True, "v1", "2026-01-01T00:00:00"))
    assert svc.has_consent("u", "p") is True
    svc.record(ConsentRecord("u", "p", False, "v1", "2026-02-01T00:00:00"))
    assert svc.has_consent("u", "p") is False


def test_adverse_action_reasons_from_low_scores():
    result = AssessmentEngine(INCLUSION_READINESS_CONFIG).evaluate(
        {
            **{r.metric: 1.0 for r in INCLUSION_READINESS_CONFIG.rules},
            "disparate_impact_testing": 0.0,
        }
    )
    reasons = AdverseActionReasoner().reasons(result)
    assert any(r.code == "bias_testing" for r in reasons)


def test_four_fifths_flags_disparate_impact():
    di = four_fifths_check({"A": 80, "B": 50}, {"A": 100, "B": 100})
    assert not di.passes and "B" in di.flagged_groups


# -- the 10 family scorecards ----------------------------------------------


def test_ten_family_configs_present():
    assert len(FAMILY_CONFIGS) == 10


def test_every_family_config_builds_and_scores():
    """Each family config must be structurally valid and fully answerable."""
    for slug, config in FAMILY_CONFIGS.items():
        engine = AssessmentEngine(config)  # raises on orphaned/invalid config
        # Answering every question '1.0' should yield a perfect, complete score.
        answers = {r.metric: 1.0 for r in config.rules}
        result = engine.evaluate(answers)
        assert not result.missing_inputs, f"{slug} has unmapped metrics"
        assert result.composite_score == 100.0, f"{slug} did not reach 100"
        # And every rule must carry a regulatory ref or reasoning (explainable).
        for dim in result.dimension_results:
            for rr in dim.rule_results:
                assert rr.reasoning
