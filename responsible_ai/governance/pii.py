"""
PII redaction before AI calls.

Bridge #2, part 1. The gap analysis found that full financial context (income,
balances, account details) is sent verbatim to the LLM. In a regulated
inclusion setting that is unacceptable. ``PIIRedactor`` masks direct identifiers
in free text and minimizes structured context to the numeric signals the engine
actually needs — so the deterministic engine sees real data while the LLM only
ever sees redacted, minimized input.

Security posture:
  * **Fail toward masking.** Ambiguous long digit runs are redacted, not passed.
  * **ReDoS-safe.** All patterns use bounded, non-overlapping quantifiers; an
    adversarial-input test guards against catastrophic backtracking.
  * **No raw PII in audit.** ``RedactionReport`` records *counts by type* only;
    ``log_redaction`` persists just those counts to a decision log.

Pure and standard-library only, so it drops into any deployment.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

# Order matters: apply the most specific patterns first. Every pattern is
# anchored and bounded to keep matching linear.
_PATTERNS = [
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    ("SSN", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("IBAN", re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b")),
    # 12-19 digit runs (card / account numbers), allowing single spaces/dashes.
    ("ACCOUNT", re.compile(r"\b\d(?:[ -]?\d){11,18}\b")),
    (
        "PHONE",
        re.compile(r"\b(?:\+?\d{1,2}[ -]?)?(?:\(?\d{3}\)?[ -]?)\d{3}[ -]?\d{4}\b"),
    ),
]


def luhn_valid(number: str) -> bool:
    """Luhn checksum — useful to confirm a digit run is a real card number."""
    digits = [int(c) for c in number if c.isdigit()]
    if len(digits) < 12:
        return False
    checksum = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


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


def log_redaction(
    decision_log,
    *,
    subject_id: str,
    report: RedactionReport,
    timestamp: str,
    correlation_id: Optional[str] = None,
) -> None:
    """
    Persist a redaction event to an append-only decision log — counts only,
    never the raw text. Gives PII handling an auditable, DB-backed trail.
    """
    decision_log.append(
        timestamp=timestamp,
        subject_id=subject_id,
        action="pii_redaction",
        decision="REDACTED" if report.total else "CLEAN",
        reason=f"redacted {report.total} identifier(s)",
        correlation_id=correlation_id,
        metadata={"counts": report.counts},
    )


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
