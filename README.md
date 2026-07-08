# LFSD — an open, modular responsible-AI framework for inclusive finance

**LFSD (Life Financial Services Decisions)** is the reference implementation of an
open, community-governed framework for responsible, AI-assisted financial
decision-support — built so that institutions without large AI teams
(community banks, credit unions, CDFIs, and mission-driven fintechs) can adopt
inclusive financial technology with governance built in, not bolted on.

This is an early-stage, working proof of concept under active development. It is
open-source (MIT), openly governed, and not a commercial product: no single
entity controls the codebase or roadmap. See [`GOVERNANCE/`](GOVERNANCE/).

## What's in this repository

**1. The framework modules (the reusable core)**
- [`packages/responsible-ai`](packages/responsible-ai) — a standalone,
  pip-installable governance layer: consent management and PII redaction,
  designed to sit in front of any model call. This is the first framework
  module extracted for independent reuse.
- **Decision engine** — a policy-first, AI-assisted architecture: deterministic
  rules and institutional policy constraints govern outcomes; AI assists with
  intake, classification, explanation, and decision support. High-impact
  decisions are never delegated to a model. See
  [`docs/DECISION_ENGINE.md`](docs/DECISION_ENGINE.md).
- **Scoring dimensions** — transparent, explainable scoring across three
  dimensions of financial wellbeing: **time, wealth, and health** — the basis
  for personalized, auditable guidance rather than black-box recommendations.

**2. Helmory (the demonstration deployment)**
[Helmory](https://app.helmory.com) is the consumer-facing demo that exercises
the framework end-to-end — onboarding, financial goals, and day-to-day
decision support. It exists to prove the architecture works in operation;
the framework, not the demo, is the contribution.

## Design principles

- **Policy-first, AI-assisted.** Deterministic controls above probabilistic
  models. The system never fabricates data and never auto-executes
  high-impact financial decisions.
- **Governance as architecture.** Consent, auditability, explainability, and
  human oversight are framework components, not compliance afterthoughts.
- **Built for resource-constrained institutions.** Modules are independently
  adoptable, vendor-neutral, and designed for institutions that consume
  technology through vendors rather than building it.
- **Open by default.** MIT-licensed, community-governed, with security
  scanning on every PR ([`SECURITY.md`](SECURITY.md)).

## Status and roadmap

Current stage: research-and-maturation. The inclusion-focused modules
(onboarding, financial goals, financial-wellness scoring) lead; a
credit-relevant decision-support module is a research objective requiring
fair-lending controls, model-governance review, and regulator engagement
before any deployment.

Contributions, issues, and adoption experiments are welcome.
