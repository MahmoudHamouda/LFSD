# responsible-ai

A modular, **policy-first** Responsible-AI toolkit for financial-inclusion work —
deterministic, explainable scoring plus the governance controls a regulated
institution needs (consent, PII redaction, a policy gate, and fair-lending
controls). It depends on nothing in any host application and is meant to be
lifted into your own codebase.

## Install

```bash
# core (scoring + pure-logic governance) — no third-party deps
pip install "git+https://github.com/MahmoudHamouda/LFSD.git#subdirectory=packages/responsible-ai"

# with the DB-backed stores (SQLAlchemy)
pip install "responsible-ai[db] @ git+https://github.com/MahmoudHamouda/LFSD.git#subdirectory=packages/responsible-ai"
```

Or from a clone:

```bash
cd packages/responsible-ai && pip install ".[db]"
```

## Quick start

```bash
python -m responsible_ai.scoring.demo        # one engine, two scorecards
python -m responsible_ai.governance.demo     # consent + policy gate + tamper check (needs [db])
```

Full documentation lives in [`responsible_ai/README.md`](responsible_ai/README.md),
with `ARCHITECTURE.md`, `ADOPTION_GUIDE.md`, and `governance/SECURITY.md` alongside it.
