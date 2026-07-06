"""
PII redaction before AI calls.

Bridge #2, part 1. The gap analysis found that full financial context (income,
balances, account details) is sent verbatim to the LLM. In a regulated
inclusion setting that is unacceptable. ``PIIRedactor`` masks direct identifiers
in free text and minimizes structured context to the numeric signals the engine
actually needs — so the deterministic engine sees real data while the LLM only
ever sees redacted, minimized input.

Deterministic and dependency-free so it drops into any deployment.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List

# Order matters: apply the most specific patterns first.
_PATTERNS = [
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    # 12-19 digit runs (card / account numbers), allowing spaces or dashes.
    ("ACCOUNT", re.compile(r"\b(?:\d[ -]?){12,19}\b")),
    (
        "PHONE",
        re.compile(r"\b(?:\+?\d{1,2}[ -]?)?(?:\(?\d{3}\)?[ -]?)\d{3}[ -]?\d{4}\b"),
    ),
    ("IBAN", re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b")),
]


@dataclass
class RedactionReport:
    """What was redacted — itself auditable, contains no raw PII."""

    text: str
    counts: Dict[str, int] = field(default_factory=dict)

    @property
    def total(self) -> int:
        return sum(self.counts.values())


class PIIRedactor:
    """Masks direct identifiers in text and minimizes structured context."""

    def redact_text(self, text: str) -> RedactionReport:
        """Replace detected identifiers with ``[TYPE_REDACTED]`` tokens."""
        counts: Dict[str, int] = {}
        out = text or ""
        for label, pattern in _PATTERNS:
            out, n = pattern.subn(f"[{label}_REDACTED]", out)
            if n:
                counts[label] = counts.get(label, 0) + n
        return RedactionReport(text=out, counts=counts)

    def minimize_context(self, context: Dict, allow: Iterable[str]) -> Dict:
        """
        Data-minimization for structured prompts: keep only the allow-listed
        keys (the aggregate signals the model needs — e.g. ``savings_rate``,
        ``emergency_fund_months``) and drop everything else (raw transactions,
        account numbers, names). Default-deny.
        """
        allow_set = set(allow)
        return {k: v for k, v in (context or {}).items() if k in allow_set}

    def scrub_prompt(self, prompt: str) -> str:
        """Convenience: redact a fully-rendered prompt string."""
        return self.redact_text(prompt).text


# Signals the LLM is permitted to see for financial advisory — aggregates only,
# never raw identifiers or line-item data. An FI can tune this allow-list.
DEFAULT_FINANCIAL_ALLOWLIST: List[str] = [
    "savings_rate",
    "emergency_fund_months",
    "debt_to_income",
    "invested_ratio",
    "monthly_income_band",
    "expense_ratio",
    "composite_score",
]
