"""
Per-family readiness scorecards — one per concept-note use-case family.

The cross-cutting ``INCLUSION_READINESS_CONFIG`` scores an institution's overall
governance posture. These ten configs go a level deeper: each scores readiness
for a *specific* inclusion use case, using questions drawn from that family's
description in the concept note. Every config is deterministic and explainable
via the same ``AssessmentEngine``, and is illustrative — an FI forks and tunes.

Answer scale for every question: 0.0 = absent, 0.5 = partial, 1.0 = in place.

Use ``FAMILY_CONFIGS`` (slug -> AssessmentConfig) to enumerate them.
"""

from __future__ import annotations

from ..schema import AssessmentConfig, Dimension
from ._common import question as q


# 1 -------------------------------------------------------------------------
ACCOUNT_ONBOARDING = AssessmentConfig(
    name="Account Access & Digital Onboarding readiness",
    version="0.1.0",
    owner="Responsible-AI framework",
    description="e-KYC, branch-light journeys, plain-language flows, consented data.",
    dimensions=[
        Dimension(name="Identity & KYC", weight=1.5),
        Dimension(name="Journey & Access", weight=1.0),
        Dimension(name="Data & Consent", weight=1.2),
    ],
    rules=[
        q(
            "ekyc_readiness",
            "Identity & KYC",
            "ekyc_readiness",
            "Is e-KYC / identity verification in place for digital onboarding?",
            "No e-KYC capability.",
            "Manual/partial identity checks.",
            "Automated e-KYC with document verification.",
            weight=1.5,
            regulatory_ref="CIP / BSA-AML",
        ),
        q(
            "sanctions_screening",
            "Identity & KYC",
            "sanctions_screening",
            "Are applicants screened against sanctions/watchlists?",
            "No screening.",
            "Manual screening.",
            "Automated OFAC/watchlist screening.",
        ),
        q(
            "branch_light",
            "Journey & Access",
            "branch_light_journey",
            "Can an account be opened end-to-end without a branch visit?",
            "Branch required.",
            "Partial digital journey.",
            "Fully digital journey.",
        ),
        q(
            "plain_language",
            "Journey & Access",
            "multilingual_plain_language",
            "Are flows multilingual and plain-language?",
            "English-only, jargon-heavy.",
            "Some plain-language.",
            "Multilingual, plain-language flows.",
        ),
        q(
            "abandonment_metrics",
            "Journey & Access",
            "abandonment_measurement",
            "Is onboarding completion/drop-off measured?",
            "Not measured.",
            "Basic funnel view.",
            "Instrumented completion/drop-off.",
        ),
        q(
            "consented_sources",
            "Data & Consent",
            "consented_data_sources",
            "Are external data sources consented and permissible?",
            "Unconfirmed.",
            "Some reviewed.",
            "All consented and permissible.",
            regulatory_ref="GLBA",
        ),
    ],
)

# 2 -------------------------------------------------------------------------
CASHFLOW_SAVINGS = AssessmentConfig(
    name="Cash-flow Resilience & Emergency Savings readiness",
    version="0.1.0",
    owner="Responsible-AI framework",
    description="Transaction-pattern review, opt-in nudges, goal-based micro-saving.",
    dimensions=[
        Dimension(name="Data Signals", weight=1.2),
        Dimension(name="Intervention Design", weight=1.0),
        Dimension(name="Measurement", weight=1.0),
    ],
    rules=[
        q(
            "cashflow_data",
            "Data Signals",
            "cashflow_pattern_data",
            "Is transaction/cash-flow data available and clean enough to analyze?",
            "No usable cash-flow data.",
            "Partial/dirty data.",
            "Clean cash-flow data.",
        ),
        q(
            "volatility_detection",
            "Data Signals",
            "volatility_detection",
            "Can income volatility / predictable shortfalls be detected?",
            "No detection.",
            "Ad-hoc detection.",
            "Systematic volatility detection.",
        ),
        q(
            "optin_nudges",
            "Intervention Design",
            "nudge_design_optin",
            "Are savings nudges opt-in and non-intrusive by design?",
            "No nudge design / dark patterns.",
            "Nudges exist, not clearly opt-in.",
            "Transparent, opt-in nudges.",
        ),
        q(
            "micro_savings",
            "Intervention Design",
            "goal_micro_savings",
            "Are goal-based / micro-savings journeys available?",
            "None.",
            "Basic savings goals.",
            "Goal-based micro-saving journeys.",
        ),
        q(
            "resilience_metrics",
            "Measurement",
            "overdraft_measurement",
            "Are outcomes (activation, recurring contributions, overdraft reduction) measured?",
            "Not measured.",
            "Some metrics.",
            "Leading & lagging metrics instrumented.",
        ),
    ],
)

# 3 -------------------------------------------------------------------------
CREDIT_THINFILE = AssessmentConfig(
    name="Credit Access & Thin-file Decision Support readiness",
    version="0.1.0",
    owner="Responsible-AI framework",
    description="Alternative data, affordability, explainability, fair-lending.",
    dimensions=[
        Dimension(name="Data & Signals", weight=1.2),
        Dimension(name="Fair-Lending", weight=1.8),
        Dimension(name="Governance", weight=1.5),
    ],
    rules=[
        q(
            "alt_data",
            "Data & Signals",
            "alt_data_permissible",
            "Can alternative/supplemental data be used responsibly and permissibly?",
            "Not assessed.",
            "Some sources vetted.",
            "Permissibility confirmed & documented.",
            regulatory_ref="FCRA permissible purpose",
        ),
        q(
            "repayment_signals",
            "Data & Signals",
            "repayment_signals",
            "Are repayment / bill-payment / cash-flow signals available?",
            "None.",
            "Some signals.",
            "Rich repayment/affordability signals.",
        ),
        q(
            "adverse_action",
            "Fair-Lending",
            "adverse_action_ready",
            "Can specific, accurate adverse-action reasons be produced?",
            "No.",
            "Generic reasons.",
            "Specific, model-derived reasons.",
            weight=1.5,
            regulatory_ref="ECOA / FCRA adverse action",
        ),
        q(
            "disparate_impact",
            "Fair-Lending",
            "disparate_impact_testing",
            "Is disparate-impact / fairness testing performed and monitored?",
            "None.",
            "One-off review.",
            "Ongoing monitoring.",
            weight=1.5,
            regulatory_ref="ECOA / Reg B",
        ),
        q(
            "human_review",
            "Governance",
            "human_review_decision",
            "Is final credit approval reserved for humans (no automated denial)?",
            "Automated decisions.",
            "Some human review.",
            "Human-in-the-loop for all decisions.",
        ),
        q(
            "explainability",
            "Governance",
            "explainability",
            "Do decision-support outputs trace to explicit criteria?",
            "Black-box.",
            "Partial rationale.",
            "Fully traceable to named criteria.",
        ),
    ],
)

# 4 -------------------------------------------------------------------------
SME_FINANCE = AssessmentConfig(
    name="SME / MSME Finance readiness",
    version="0.1.0",
    owner="Responsible-AI framework",
    description="SME onboarding, cash-flow underwriting, merchant analytics, embedded finance.",
    dimensions=[
        Dimension(name="Onboarding & Data", weight=1.2),
        Dimension(name="Underwriting", weight=1.3),
        Dimension(name="Partnerships", weight=1.0),
    ],
    rules=[
        q(
            "sme_onboarding",
            "Onboarding & Data",
            "sme_onboarding",
            "Is there a digital SME onboarding path?",
            "None.",
            "Manual/partial.",
            "Digital SME onboarding.",
        ),
        q(
            "cashflow_underwriting",
            "Underwriting",
            "cashflow_underwriting_data",
            "Is SME cash-flow data available for underwriting?",
            "No standardized records.",
            "Partial data.",
            "Standardized cash-flow histories.",
        ),
        q(
            "merchant_analytics",
            "Underwriting",
            "merchant_analytics",
            "Are merchant/transaction analytics available?",
            "None.",
            "Basic.",
            "Rich merchant analytics.",
        ),
        q(
            "embedded_finance",
            "Partnerships",
            "embedded_finance_partners",
            "Are procurement/marketplace or embedded-finance partnerships available?",
            "None.",
            "Exploratory.",
            "Established partnerships.",
        ),
    ],
)

# 5 -------------------------------------------------------------------------
FRAUD_ANOMALY = AssessmentConfig(
    name="Fraud, Anomaly & Early-risk Detection readiness",
    version="0.1.0",
    owner="Responsible-AI framework",
    description="Anomaly detection and telemetry without turning inclusion into risk.",
    dimensions=[
        Dimension(name="Detection", weight=1.3),
        Dimension(name="Controls", weight=1.2),
        Dimension(name="Operations", weight=1.0),
    ],
    rules=[
        q(
            "anomaly_detection",
            "Detection",
            "anomaly_detection",
            "Is anomaly/suspicious-behavior detection in place?",
            "None.",
            "Rules-only/basic.",
            "Anomaly detection with telemetry.",
        ),
        q(
            "distress_signals",
            "Detection",
            "consumer_distress_signals",
            "Can early signs of consumer distress be identified (not just fraud)?",
            "No.",
            "Partial.",
            "Systematic distress signals.",
        ),
        q(
            "false_positive_mgmt",
            "Controls",
            "false_positive_monitoring",
            "Are false-positive rates monitored to avoid excluding good customers?",
            "Not monitored.",
            "Occasionally.",
            "Continuously monitored.",
        ),
        q(
            "escalation_coverage",
            "Controls",
            "escalation_coverage",
            "Is there defined escalation coverage for flagged cases?",
            "None.",
            "Partial.",
            "Full escalation coverage.",
        ),
        q(
            "audit_readiness",
            "Operations",
            "audit_readiness",
            "Are detections and dispositions auditable?",
            "No.",
            "Partial logs.",
            "Fully auditable.",
        ),
    ],
)

# 6 -------------------------------------------------------------------------
RESPONSIBLE_AI_OPS = AssessmentConfig(
    name="Responsible AI, Compliance & Auditability readiness",
    version="0.1.0",
    owner="Responsible-AI framework",
    description="Model governance, bias checks, explainability, consent, escalation, audit logs.",
    dimensions=[
        Dimension(name="Model Governance", weight=1.5),
        Dimension(name="Explainability & Fairness", weight=1.5),
        Dimension(name="Oversight & Audit", weight=1.2),
    ],
    rules=[
        q(
            "model_inventory",
            "Model Governance",
            "model_inventory",
            "Is there a model inventory with versioning and approval?",
            "None.",
            "Ad-hoc.",
            "Inventory + versioning + approval.",
            regulatory_ref="SR 11-7",
        ),
        q(
            "drift_monitoring",
            "Model Governance",
            "drift_monitoring",
            "Is model/performance drift monitored?",
            "No.",
            "Manual checks.",
            "Automated drift monitoring.",
        ),
        q(
            "bias_checks",
            "Explainability & Fairness",
            "bias_checks",
            "Are bias/fairness checks run and monitored?",
            "None.",
            "One-off.",
            "Ongoing.",
            weight=1.5,
            regulatory_ref="ECOA / Reg B",
        ),
        q(
            "explainability_reqs",
            "Explainability & Fairness",
            "explainability_reqs",
            "Are explainability requirements defined and met?",
            "None.",
            "Partial.",
            "Defined and enforced.",
        ),
        q(
            "escalation_rules",
            "Oversight & Audit",
            "escalation_rules",
            "Are human escalation rules defined for high-risk outputs?",
            "None.",
            "Informal.",
            "Documented escalation rules.",
        ),
        q(
            "audit_logs",
            "Oversight & Audit",
            "audit_logs",
            "Are AI decisions captured in immutable audit logs?",
            "None.",
            "Partial.",
            "Immutable, complete audit logs.",
        ),
    ],
)

# 7 -------------------------------------------------------------------------
OPEN_BANKING = AssessmentConfig(
    name="Open Banking, Data Sharing & Interoperability readiness",
    version="0.1.0",
    owner="Responsible-AI framework",
    description="Consent flows, API readiness, core-system integration, privacy-preserving data.",
    dimensions=[
        Dimension(name="Data & Consent", weight=1.3),
        Dimension(name="Integration", weight=1.2),
        Dimension(name="Privacy", weight=1.2),
    ],
    rules=[
        q(
            "consent_flows",
            "Data & Consent",
            "consent_flows",
            "Are data-sharing consent flows implemented and revocable?",
            "None.",
            "Basic consent.",
            "Revocable, auditable consent flows.",
        ),
        q(
            "api_readiness",
            "Integration",
            "api_readiness",
            "Is the institution API-ready for open-banking data exchange?",
            "No APIs.",
            "Partial.",
            "API-ready.",
        ),
        q(
            "core_integration",
            "Integration",
            "core_system_integration",
            "Is integration with the core system (e.g. Fiserv, Jack Henry) feasible?",
            "Blocked by core.",
            "Workarounds only.",
            "Supported integration path.",
        ),
        q(
            "privacy_preserving",
            "Privacy",
            "privacy_preserving_structures",
            "Are privacy-preserving data structures used?",
            "Raw data shared.",
            "Some minimization.",
            "Privacy-preserving by design.",
        ),
        q(
            "vendor_lockin",
            "Privacy",
            "vendor_lockin_mitigation",
            "Is vendor lock-in mitigated (portable data/contracts)?",
            "Locked in.",
            "Partial portability.",
            "Portable, low lock-in.",
        ),
    ],
)

# 8 -------------------------------------------------------------------------
FINTECH_EVALUATION = AssessmentConfig(
    name="Bank-Fintech Collaboration & Startup Evaluation readiness",
    version="0.1.0",
    owner="Responsible-AI framework",
    description="Structured criteria for evaluating fintech partners and integration risk.",
    dimensions=[
        Dimension(name="Partner Criteria", weight=1.2),
        Dimension(name="Integration Risk", weight=1.3),
        Dimension(name="Fit", weight=1.0),
    ],
    rules=[
        q(
            "eval_criteria",
            "Partner Criteria",
            "partner_eval_criteria",
            "Is there a structured partner-evaluation rubric?",
            "None.",
            "Informal.",
            "Documented rubric.",
        ),
        q(
            "startup_readiness",
            "Partner Criteria",
            "startup_readiness",
            "Is partner operational/financial readiness assessed?",
            "Not assessed.",
            "Partial.",
            "Assessed.",
        ),
        q(
            "integration_risk",
            "Integration Risk",
            "integration_risk",
            "Is integration/security risk assessed before onboarding a partner?",
            "No.",
            "Partial.",
            "Formal integration-risk assessment.",
        ),
        q(
            "data_strategy",
            "Integration Risk",
            "partner_data_strategy",
            "Is the partner's data strategy and data-sharing model reviewed?",
            "No.",
            "Partial.",
            "Reviewed.",
        ),
        q(
            "customer_fit",
            "Fit",
            "customer_fit",
            "Is customer/mission fit evaluated?",
            "No.",
            "Informal.",
            "Evaluated against mission.",
        ),
    ],
)

# 9 -------------------------------------------------------------------------
FINANCIAL_LITERACY = AssessmentConfig(
    name="Financial Literacy & Guided Engagement readiness",
    version="0.1.0",
    owner="Responsible-AI framework",
    description="Personalized, human-readable guidance, reminders, and education journeys.",
    dimensions=[
        Dimension(name="Content", weight=1.0),
        Dimension(name="Personalization", weight=1.2),
        Dimension(name="Measurement", weight=1.0),
    ],
    rules=[
        q(
            "education_journeys",
            "Content",
            "education_journeys",
            "Are structured financial-education journeys available?",
            "None.",
            "Static tips.",
            "Structured journeys.",
        ),
        q(
            "plain_language",
            "Content",
            "plain_language_guidance",
            "Is guidance human-readable and plain-language?",
            "Jargon-heavy.",
            "Some.",
            "Consistently plain-language.",
        ),
        q(
            "behavioral_insights",
            "Personalization",
            "behavioral_insights",
            "Is guidance personalized using behavioral insights?",
            "Generic.",
            "Basic segmentation.",
            "Behaviorally personalized.",
        ),
        q(
            "reminders",
            "Personalization",
            "reminders",
            "Are timely, opt-in reminders/prompts available?",
            "None.",
            "Basic.",
            "Timely, opt-in prompts.",
        ),
        q(
            "comprehension",
            "Measurement",
            "comprehension_measurement",
            "Is customer understanding/engagement measured?",
            "Not measured.",
            "Engagement only.",
            "Comprehension & engagement measured.",
        ),
    ],
)

# 10 ------------------------------------------------------------------------
DIGITAL_WEALTH = AssessmentConfig(
    name="Digital Wealth & Long-term Asset Building readiness",
    version="0.1.0",
    owner="Responsible-AI framework",
    description="Low-cost goal-based savings, investment education, retirement readiness.",
    dimensions=[
        Dimension(name="Access & Education", weight=1.2),
        Dimension(name="Goals", weight=1.0),
        Dimension(name="Suitability", weight=1.3),
    ],
    rules=[
        q(
            "low_cost_access",
            "Access & Education",
            "low_cost_access",
            "Is low-cost access to long-term products available to underserved users?",
            "None.",
            "High-cost only.",
            "Low-cost access.",
        ),
        q(
            "investment_education",
            "Access & Education",
            "investment_education",
            "Is investment/retirement education provided?",
            "None.",
            "Basic.",
            "Structured education.",
        ),
        q(
            "goal_based",
            "Goals",
            "goal_based_savings",
            "Are goal-based long-term savings journeys available?",
            "None.",
            "Basic goals.",
            "Goal-based journeys.",
        ),
        q(
            "suitability",
            "Suitability",
            "suitability_controls",
            "Are suitability / appropriateness controls in place?",
            "None.",
            "Partial.",
            "Suitability controls enforced.",
            weight=1.5,
            regulatory_ref="Reg BI / suitability",
        ),
    ],
)


# Registry: slug -> config -------------------------------------------------
FAMILY_CONFIGS = {
    "account_onboarding": ACCOUNT_ONBOARDING,
    "cashflow_savings": CASHFLOW_SAVINGS,
    "credit_thinfile": CREDIT_THINFILE,
    "sme_finance": SME_FINANCE,
    "fraud_anomaly": FRAUD_ANOMALY,
    "responsible_ai_ops": RESPONSIBLE_AI_OPS,
    "open_banking": OPEN_BANKING,
    "fintech_evaluation": FINTECH_EVALUATION,
    "financial_literacy": FINANCIAL_LITERACY,
    "digital_wealth": DIGITAL_WEALTH,
}
