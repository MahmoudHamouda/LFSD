# Governance layer — security & operational readiness

These components are built to run **on their own, against a real database**,
before any integration into a request pipeline. This document states the
security properties they guarantee and the responsibilities that remain with the
deploying institution.

## Threat model (what these controls defend against)

| Risk | Control | Where |
|---|---|---|
| Acting without customer permission | Consent gate, **default-deny** | `consent.py`, `policy.py` |
| Silent edit/deletion of the consent or decision record | **Hash-chained, append-only** ledgers with `verify_chain()` | `stores.py` |
| Leaking PII to an LLM/3rd party | Redaction + data-minimization (**fail toward masking**) | `pii.py` |
| Executing a risky action without oversight | Risk-tiered gate (CONFIRM / **2FA** for CRITICAL) | `policy.py` |
| Replay / double-execution | Idempotency keys (first-writer-wins) | `stores.py`, `policy.py` |
| SQL injection | Parameterized SQLAlchemy Core only; no string SQL | `stores.py` |
| Denial of service via crafted text (ReDoS) | Bounded, non-overlapping regex; adversarial test | `pii.py` |
| PII landing in the audit trail | Ledgers store pseudonymous ids, decisions, and **counts** only | `stores.py`, `pii.py` |

## Guarantees

1. **Default-deny.** No consent record ⇒ `has_consent` is `False`. Unknown
   action ⇒ policy `DENY`. Missing store ⇒ deny. Nothing is permitted implicitly.
2. **Append-only + tamper-evident.** `SqlConsentStore` and `SqlDecisionLog`
   expose only append and read. Each row is `sha256(canonical_row + prev_hash)`;
   `verify_chain()` recomputes the chain and returns `False` on any edit,
   re-order, or deletion. (Demonstrated in `demo.py` and `tests/`.)
3. **Determinism.** Given the same config, inputs, and consent state, the gate
   and the assessment engine always return the same decision — reproducible for
   audit.
4. **Fail-safe logging.** If writing the decision log throws, the *decision
   still stands*; logging never changes or blocks the gate outcome.
5. **PII stays out of the model and the log.** `minimize_context` is an
   allow-list (default-deny of fields); `redact_text` masks direct identifiers;
   `log_redaction` records only counts by type.

## Operational readiness checklist

- [x] Runs against any SQLAlchemy engine; `create_all()` provisions tables.
- [x] Verified on SQLite; portable to Postgres (Core only, no dialect features).
- [x] Unit + DB round-trip + tamper + ReDoS tests (`tests/test_governance_db.py`).
- [x] Standalone demo (`governance/demo.py`).
- [x] No imports from any host application.

## Responsibilities that remain with the deployer

- **Transport & auth.** Put the consent-capture and decision surfaces behind
  authenticated, TLS-terminated endpoints. These modules authorize; they do not
  authenticate.
- **Timestamps.** Callers supply ISO-8601 timestamps (the modules are
  clock-injectable for testability); use a trusted server clock in production.
- **Concurrency.** The hash chain assumes appends are serialized per table. On
  Postgres, wrap appends in a transaction with appropriate row locking, or route
  writes through a single writer, for high-concurrency deployments.
- **At-rest encryption & backups.** Provided by your database; enable them.
- **Protected-class data.** Fairness monitoring (`fairness.py`) needs group
  labels you must source and govern under your own policy.
- **Key management.** If you extend records with signatures/HMAC, manage keys in
  your KMS.
