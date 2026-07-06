# Architecture

The framework is deliberately small and has one governing rule:

> **Deterministic policy at the center; AI only at the edges.**

## The flow

```
                    ┌─────────────────────────────────────────┐
   inputs ─────────▶│  1. GOVERNANCE (pre)                     │
  (data / answers)  │     consent check · PII minimization     │
                    └───────────────────┬─────────────────────┘
                                        ▼
                    ┌─────────────────────────────────────────┐
                    │  2. ASSESSMENT ENGINE (deterministic)    │
                    │     config → rules → bands → scores      │
                    │     100% traceable, no LLM               │
                    └───────────────────┬─────────────────────┘
                                        ▼
                    ┌─────────────────────────────────────────┐
                    │  3. GOVERNANCE (post)                    │
                    │     adverse-action reasons · fairness    │
                    │     monitoring · audit record            │
                    └───────────────────┬─────────────────────┘
                                        ▼
                    ┌─────────────────────────────────────────┐
                    │  4. AI (optional, edge only)             │
                    │     plain-language wrapper over the      │
                    │     already-decided, redacted result     │
                    └─────────────────────────────────────────┘
```

The AI never decides anything. By the time an LLM is (optionally) called, the
score and its rationale already exist and the input is redacted. This is what
makes the system defensible: pull the LLM out entirely and the decision,
explanation, and audit trail are unchanged.

## Components

### `scoring/` — the assessment method

- **`AssessmentConfig`** is *data*, not code: dimensions (weighted groups) and
  rules (a metric → 0-100 score via declarative `Band`s). Because policy lives
  in config, the config *is* the auditable artifact.
- **`AssessmentEngine`** is stateless and knows nothing about finance, health,
  or inclusion. Same code, any config.
- **`AssessmentResult`** carries the composite score, per-dimension and per-rule
  breakdown, each with `reasoning` and an optional `regulatory_ref`.
  `.explain()` renders the rationale; `.to_dict()` serializes it for storage.

Determinism guarantee: identical `(config, inputs)` always yield an identical
result. Missing inputs score 0 and are reported — never silently dropped.

### `governance/` — the controls

- **`pii.PIIRedactor`** — masks direct identifiers in free text and minimizes a
  structured context dict to an allow-list of aggregate signals, so the engine
  sees real data while any downstream LLM sees only redacted, minimized input.
- **`consent.ConsentService`** — append-only, versioned consent keyed by
  `(user, purpose)`. Default-deny; latest record wins; withdrawal is a new
  record, so the ledger is a complete history.
- **`fairness.AdverseActionReasoner`** — turns the lowest-scoring rules of an
  assessment into specific, accurate adverse-action statements (ECOA/FCRA
  require the *real* factors). **`four_fifths_check`** monitors disparate impact
  across groups.

## Where it plugs into an existing app

The framework is standalone (no imports from the host app). To integrate:

1. Call `ConsentService.has_consent(...)` before processing.
2. Build the engine's `inputs` from your data; run `AssessmentEngine.evaluate`.
3. Persist `result.to_dict()` to your audit store (HELM uses `AuditLog` /
   `intelligence_traces`).
4. If declining an action, attach `AdverseActionReasoner.reasons(result)`.
5. Before any LLM call, run the prompt/context through `PIIRedactor`.

Nothing above requires the LLM to be present or correct.
