"""
FI-facing config: Responsible-AI Inclusion Readiness scorecard.

This is the "taste" for a financial institution. The *same* AssessmentEngine
that produces the consumer Viv score here produces the concept note's headline
artifact — a readiness scorecard an institution can run before piloting an
AI-assisted inclusion use case.

Inputs are yes/no or 0-1 maturity answers to structured review questions (the
"review questions and scorecards" the framework promises). Each rule cites the
governance concern it maps to, so the output doubles as a gap list. This config
is illustrative — an FI is expected to fork and tune it.

Metric convention: answers are 0..1 maturity levels
    0.0 = absent, 0.5 = partial/in-progress, 1.0 = in place and evidenced.
"""

from __future__ import annotations

from ..schema import AssessmentConfig, Band, Dimension, Rule


def _maturity_bands(absent_reason, partial_reason, ready_reason):
    """Standard 0/0.5/1.0 maturity bands for a readiness question."""
    return [
        Band(max_value=0.0, score=0, reasoning=absent_reason),
        Band(max_value=0.5, score=50, reasoning=partial_reason),
        Band(max_value=None, score=100, reasoning=ready_reason),
    ]


INCLUSION_READINESS_CONFIG = AssessmentConfig(
    name="Responsible-AI Inclusion Readiness",
    version="0.1.0",
    owner="Responsible-AI framework",
    description=(
        "Pre-pilot readiness scorecard for an AI-assisted financial-inclusion "
        "use case. Scores an institution across data, governance, fair-lending, "
        "privacy/consent, and operational readiness. Illustrative — fork and tune."
    ),
    changelog=["0.1.0 — initial reference scorecard."],
    dimensions=[
        Dimension(
            name="Data Readiness",
            weight=1.0,
            description="Data quality, coverage, consent to use.",
        ),
        Dimension(
            name="Governance",
            weight=1.5,
            description="Model governance, auditability, human oversight.",
        ),
        Dimension(
            name="Fair-Lending",
            weight=1.5,
            description="Bias controls and adverse-action readiness.",
        ),
        Dimension(
            name="Privacy & Consent",
            weight=1.2,
            description="Consent capture, PII handling, retention.",
        ),
        Dimension(
            name="Operational",
            weight=1.0,
            description="Explainability, escalation, measurement.",
        ),
    ],
    rules=[
        # -- Data Readiness ------------------------------------------------
        Rule(
            id="data_quality",
            dimension="Data Readiness",
            metric="data_quality_documented",
            description="Is data quality/coverage for the use case assessed and documented?",
            bands=_maturity_bands(
                "No data-quality assessment for this use case.",
                "Partial/informal data-quality view.",
                "Documented data-quality and coverage assessment in place.",
            ),
        ),
        Rule(
            id="permissible_data",
            dimension="Data Readiness",
            metric="permissible_data_confirmed",
            description="Are all data sources permissible and consented for this use?",
            regulatory_ref="GLBA / FCRA permissible purpose",
            bands=_maturity_bands(
                "Permissibility of data sources not confirmed.",
                "Some sources reviewed for permissibility.",
                "All data sources confirmed permissible and consented.",
            ),
        ),
        # -- Governance ----------------------------------------------------
        Rule(
            id="model_governance",
            dimension="Governance",
            metric="model_governance_process",
            description="Is there a model inventory/versioning and approval process?",
            regulatory_ref="SR 11-7 model risk management",
            bands=_maturity_bands(
                "No model governance process.",
                "Ad-hoc model tracking, no formal approval.",
                "Model inventory, versioning, and approval workflow in place.",
            ),
        ),
        Rule(
            id="audit_trail",
            dimension="Governance",
            metric="decision_audit_trail",
            description="Are AI-assisted decisions captured in an immutable audit trail?",
            bands=_maturity_bands(
                "No audit trail for AI-assisted decisions.",
                "Partial logging, not immutable/complete.",
                "Immutable, complete decision audit trail (provided by this framework).",
            ),
        ),
        Rule(
            id="human_oversight",
            dimension="Governance",
            metric="human_in_the_loop",
            description="Do consequential decisions require human review/approval?",
            bands=_maturity_bands(
                "AI outputs used without required human review.",
                "Human review for some decisions.",
                "Documented human-in-the-loop gates for consequential decisions.",
            ),
        ),
        # -- Fair-Lending --------------------------------------------------
        Rule(
            id="bias_testing",
            dimension="Fair-Lending",
            metric="disparate_impact_testing",
            description="Is disparate-impact / fairness testing performed and monitored?",
            regulatory_ref="ECOA / Reg B",
            bands=_maturity_bands(
                "No fairness/disparate-impact testing.",
                "One-off fairness review, not monitored.",
                "Ongoing disparate-impact testing and monitoring.",
            ),
        ),
        Rule(
            id="adverse_action",
            dimension="Fair-Lending",
            metric="adverse_action_reasons",
            description="Can the system produce specific, accurate adverse-action reasons?",
            regulatory_ref="ECOA / FCRA adverse action",
            bands=_maturity_bands(
                "No adverse-action reason generation.",
                "Generic reasons only.",
                "Specific, model-derived adverse-action reasons available.",
            ),
        ),
        # -- Privacy & Consent --------------------------------------------
        Rule(
            id="consent_capture",
            dimension="Privacy & Consent",
            metric="consent_captured_and_stored",
            description="Is customer consent captured, versioned, and stored?",
            bands=_maturity_bands(
                "Consent not captured or not stored.",
                "Consent collected but not versioned/auditable.",
                "Consent captured, versioned, and auditable (framework consent module).",
            ),
        ),
        Rule(
            id="pii_minimization",
            dimension="Privacy & Consent",
            metric="pii_minimized_to_ai",
            description="Is PII redacted/minimized before sending to any AI model?",
            bands=_maturity_bands(
                "Raw PII sent to AI models.",
                "Some fields masked, ad hoc.",
                "PII redaction/minimization enforced before AI calls (framework PII module).",
            ),
        ),
        # -- Operational ---------------------------------------------------
        Rule(
            id="explainability",
            dimension="Operational",
            metric="explanations_traceable",
            description="Do recommendations trace to explicit, named criteria?",
            bands=_maturity_bands(
                "Recommendations are black-box.",
                "Some rationale, not fully traceable.",
                "Every recommendation traces to named policy/criteria (framework engine).",
            ),
        ),
        Rule(
            id="measurement_plan",
            dimension="Operational",
            metric="measurement_plan_defined",
            description="Are leading/lagging success metrics defined for the pilot?",
            bands=_maturity_bands(
                "No measurement plan.",
                "Metrics named but not instrumented.",
                "Leading/lagging metrics defined and instrumented.",
            ),
        ),
    ],
)
