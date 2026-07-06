# Responsible-AI Framework

A modular, **policy-first** toolkit for AI-assisted financial-inclusion work,
extracted from the HELM platform. It is designed to be **lifted into your own
codebase and deployed** — there is no SaaS, no tenant model, no vendor lock-in.
You take the code and run it.

It packages the capabilities a regulated institution actually needs to adopt AI
responsibly:

1. A **deterministic, explainable scoring engine** — the same engine produces a
   consumer wellbeing score *and* an institutional readiness scorecard, purely
   from configuration.
2. A **governance layer** — PII redaction before any AI call, versioned/auditable
   consent, and fair-lending controls (adverse-action reasons + disparate-impact
   testing).

> **Design principle (from the concept note):** deterministic rules and
> scorecards sit at the center; AI is used only where it adds value (plain-language
> synthesis), never as a black-box decision-maker. Every score traces back to a
> named rule and the input that triggered it.

---

## Try it in 30 seconds

```bash
python -m responsible_ai.scoring.demo
```

This runs the *same* engine twice:

- **Consumer** — a Viv wellbeing score across Wealth / Health / Time.
- **Institution** — a Responsible-AI **inclusion-readiness scorecard** that
  scores your organization across Data, Governance, Fair-Lending, Privacy, and
  Operational readiness, and prints the top gaps to close before a pilot.

The only difference between the two runs is which **config** is passed in.

---

## What's inside

```
responsible_ai/
├── scoring/                     # Bridge #1 — the reusable assessment method
│   ├── schema.py                # AssessmentConfig / Dimension / Rule / Band / Result
│   ├── engine.py                # AssessmentEngine — deterministic, explainable
│   ├── configs/
│   │   ├── viv_wellbeing.py         # reference config: the HELM/Viv score
│   │   └── inclusion_readiness.py   # example config: an FI readiness scorecard
│   └── demo.py
├── governance/                  # Bridge #2 — the controls FIs must show
│   ├── pii.py                   # redact/minimize data before AI calls
│   ├── consent.py               # persisted, versioned, default-deny consent
│   └── fairness.py              # adverse-action reasons + four-fifths rule
├── ARCHITECTURE.md
├── ADOPTION_GUIDE.md
└── README.md
```

## How it maps to the inclusion framework

| Concept-note need | Provided here |
|---|---|
| Policy-first, AI-assisted design | `scoring/engine.py` (no LLM in scoring) |
| Readiness assessment / scorecards | `configs/inclusion_readiness.py` + engine |
| Recommendations trace to explicit criteria | `AssessmentResult.explain()`, per-rule `reasoning` |
| Responsible AI, compliance, auditability | `governance/` + your audit store |
| Fair-lending safeguards | `governance/fairness.py` |
| Privacy / consent controls | `governance/consent.py`, `governance/pii.py` |

## What this is *not* (yet)

Deliberately out of scope for this first cut (see the gap analysis):
credit/thin-file underwriting, SME finance, fraud/anomaly detection, and live
open-banking aggregation are **greenfield** — the framework gives you the
governance and scoring spine to build them on, not the models themselves.
Multi-tenancy is intentionally omitted: you deploy your own instance.

See **ADOPTION_GUIDE.md** to stand this up for your institution.
