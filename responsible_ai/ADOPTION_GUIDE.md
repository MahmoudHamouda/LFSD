# Adoption Guide (for a financial institution)

This framework is meant to be **cloned and deployed inside your own stack**.
There is no account to create and no data leaves your environment. This guide
takes you from "git clone" to a running readiness assessment and a governed
scoring pipeline.

## 0. Prerequisites

- Python 3.11+
- The `responsible_ai/` package (copy it into your backend, or install it as a
  local package). It has no third-party dependencies beyond the standard library.

## 1. Run your first readiness assessment (day one)

Answer the review questions in `scoring/configs/inclusion_readiness.py` for a
use case you're considering (each answer is `0.0` absent / `0.5` partial /
`1.0` in place):

```python
from responsible_ai.scoring import AssessmentEngine
from responsible_ai.scoring.configs import INCLUSION_READINESS_CONFIG

answers = {
    "data_quality_documented": 1.0,
    "permissible_data_confirmed": 0.5,
    "model_governance_process": 0.5,
    "decision_audit_trail": 1.0,
    "human_in_the_loop": 0.5,
    "disparate_impact_testing": 0.0,
    "adverse_action_reasons": 0.0,
    "consent_captured_and_stored": 0.5,
    "pii_minimized_to_ai": 1.0,
    "explanations_traceable": 1.0,
    "measurement_plan_defined": 0.5,
}
result = AssessmentEngine(INCLUSION_READINESS_CONFIG).evaluate(answers)
print(result.explain())          # the scorecard + rationale
print(result.to_dict())          # persist this to your governance system
```

You now have a scored, gap-listed readiness report — the artifact the framework
is built to produce.

## 2. Author your own scoring config

Copy `viv_wellbeing.py` as a template. A config is just dimensions + rules:

```python
from responsible_ai.scoring import AssessmentConfig, Dimension, Rule, Band

MY_CONFIG = AssessmentConfig(
    name="Thin-file affordability signals",
    version="0.1.0",
    owner="Credit Risk",
    dimensions=[Dimension(name="Repayment", weight=2.0),
                Dimension(name="Stability", weight=1.0)],
    rules=[
        Rule(id="ontime_bills", dimension="Repayment", metric="ontime_bill_ratio",
             description="Share of bills paid on time (12mo).",
             regulatory_ref="ECOA / Reg B",
             bands=[Band(max_value=0.8, score=40, reasoning="Frequent missed bills."),
                    Band(max_value=0.95, score=75, reasoning="Mostly on-time."),
                    Band(max_value=None, score=100, reasoning="Consistently on-time.")]),
        # ...
    ],
)
```

Guidelines:
- Keep rules **declarative** (bands) so the config stays auditable. Use the
  `scorer` callable only when bands genuinely can't express the logic.
- Put the regulation each rule supports in `regulatory_ref` — it flows into
  adverse-action reasons automatically.
- Version every change and record it in `changelog` (model-risk hygiene).

## 3. Wire in governance

```python
from responsible_ai.governance import (
    ConsentService, ConsentRecord, PIIRedactor,
    AdverseActionReasoner, four_fifths_check,
)

# a) Consent — back ConsentStore with YOUR database (example: SQLAlchemy)
#    Implement append() / history() against a consent_records table.
consent = ConsentService(MyDbConsentStore(session))
if not consent.has_consent(user_id, purpose="thin_file_underwriting"):
    raise PermissionError("No consent on file for this purpose.")

# b) Score
result = AssessmentEngine(MY_CONFIG).evaluate(inputs)

# c) Persist result.to_dict() to your immutable audit store

# d) If declining, disclose the real reasons
if result.composite_score < 60:
    reasons = AdverseActionReasoner().reasons(result)   # ECOA/FCRA-ready

# e) Before ANY LLM call, redact + minimize
safe_context = PIIRedactor().minimize_context(inputs, allow=[...])
```

Run `four_fifths_check(approvals, totals)` on a schedule over your outcomes to
monitor disparate impact across groups.

## 4. Keep AI at the edge

If you use an LLM to phrase results for customers, feed it **only** the redacted,
already-scored output. The decision, explanation, and audit record must be
complete *before* the model is called — verify this by disabling the LLM and
confirming the pipeline still produces a full, defensible result.

## 5. What you still own

The framework gives you the scoring method and governance spine. You supply:
your data pipeline, your consent-store implementation, your protected-class data
handling for fairness testing, and your model-risk sign-off. Credit/SME/fraud
models and open-banking connectors are not included — build them on top.
