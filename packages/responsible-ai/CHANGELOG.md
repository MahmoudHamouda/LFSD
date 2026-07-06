# Changelog

## 0.1.0
- Initial release.
- Scoring: config-driven, deterministic, explainable `AssessmentEngine` with a
  reference wellbeing config, a cross-cutting inclusion-readiness scorecard, and
  ten per-use-case family scorecards.
- Governance: default-deny versioned consent, PII redaction (ReDoS-safe, Luhn),
  a risk-tiered execution policy gate, and fair-lending controls (adverse-action
  reasons + four-fifths disparate-impact check).
- DB-backed stores (SQLAlchemy Core): append-only, hash-chained/tamper-evident
  consent and decision logs, plus idempotency keys.
