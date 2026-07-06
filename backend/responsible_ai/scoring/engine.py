"""
Config-driven, deterministic, explainable scoring — the engine.

``AssessmentEngine`` evaluates any ``AssessmentConfig`` against a dict of inputs
and returns a fully traceable ``AssessmentResult``. It contains **no** business
knowledge and **no** LLM calls — all policy lives in the config. This is the
generalized "policy-first, AI-assisted" core from the concept note: deterministic
rules and scorecards at the center; AI (if used at all) only wraps the output in
plain language downstream.

Design guarantees:
  * Deterministic — identical (config, inputs) always yield an identical result.
  * Explainable — every point of the composite traces to a named rule + reason.
  * Graceful — a missing input scores 0 for that rule and is reported, never
    silently dropped or crashed.
  * Reusable — the same engine scores a consumer's wellbeing and a bank's
    inclusion readiness; only the config differs.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from .schema import (
    AssessmentConfig,
    AssessmentResult,
    Band,
    DimensionResult,
    Rule,
    RuleResult,
)

logger = logging.getLogger("responsible_ai.scoring")


class AssessmentEngine:
    """Stateless evaluator for declarative assessment configs."""

    def __init__(self, config: AssessmentConfig):
        self.config = config
        self._validate_config()

    # -- public API --------------------------------------------------------

    def evaluate(self, inputs: Dict[str, float]) -> AssessmentResult:
        """
        Score ``inputs`` against the config.

        ``inputs`` maps each rule's ``metric`` to a numeric value. Unknown or
        missing metrics are handled gracefully (scored 0, flagged missing).
        """
        missing: List[str] = []
        dim_results: List[DimensionResult] = []

        rules_by_dim = self._rules_by_dimension()

        for dim in self.config.dimensions:
            rule_results: List[RuleResult] = []
            for rule in rules_by_dim.get(dim.name, []):
                rr = self._evaluate_rule(rule, inputs)
                if rr.missing_input:
                    missing.append(rule.metric)
                rule_results.append(rr)

            dim_score = self._weighted_average(
                [(rr.score, rr.weight) for rr in rule_results]
            )
            dim_results.append(
                DimensionResult(
                    name=dim.name,
                    score=dim_score,
                    weight=dim.weight,
                    rule_results=rule_results,
                )
            )

        composite = self._weighted_average([(d.score, d.weight) for d in dim_results])

        return AssessmentResult(
            config_name=self.config.name,
            config_version=self.config.version,
            composite_score=composite,
            dimension_results=dim_results,
            missing_inputs=sorted(set(missing)),
        )

    # -- rule evaluation ---------------------------------------------------

    def _evaluate_rule(self, rule: Rule, inputs: Dict[str, float]) -> RuleResult:
        raw = inputs.get(rule.metric)

        if raw is None:
            # Missing input: conservative 0, explicitly flagged — never hidden.
            return RuleResult(
                rule_id=rule.id,
                dimension=rule.dimension,
                metric=rule.metric,
                metric_value=None,
                score=0.0,
                weight=rule.weight,
                reasoning=f"No value provided for '{rule.metric}'; scored 0 pending data.",
                regulatory_ref=rule.regulatory_ref,
                missing_input=True,
            )

        try:
            value = float(raw)
        except (TypeError, ValueError):
            return RuleResult(
                rule_id=rule.id,
                dimension=rule.dimension,
                metric=rule.metric,
                metric_value=None,
                score=0.0,
                weight=rule.weight,
                reasoning=f"Value for '{rule.metric}' is not numeric; scored 0.",
                regulatory_ref=rule.regulatory_ref,
                missing_input=True,
            )

        if rule.scorer is not None:
            score, reasoning = rule.scorer(value, inputs)
        else:
            score, reasoning = self._score_bands(value, rule.bands)

        return RuleResult(
            rule_id=rule.id,
            dimension=rule.dimension,
            metric=rule.metric,
            metric_value=value,
            score=self._clamp(score),
            weight=rule.weight,
            reasoning=reasoning,
            regulatory_ref=rule.regulatory_ref,
            missing_input=False,
        )

    @staticmethod
    def _score_bands(value: float, bands: List[Band]) -> tuple:
        """First band whose max_value the metric is <= wins (None = catch-all)."""
        for band in bands:
            if band.max_value is None or value <= band.max_value:
                return band.score, band.reasoning
        # No band matched (all had finite bounds and value exceeded them all).
        return 0.0, "Value out of all defined bands; scored 0."

    # -- helpers -----------------------------------------------------------

    def _rules_by_dimension(self) -> Dict[str, List[Rule]]:
        out: Dict[str, List[Rule]] = {}
        for rule in self.config.rules:
            out.setdefault(rule.dimension, []).append(rule)
        return out

    @staticmethod
    def _weighted_average(pairs: List[tuple]) -> float:
        total_w = sum(w for _, w in pairs)
        if total_w <= 0:
            return 0.0
        return sum(s * w for s, w in pairs) / total_w

    @staticmethod
    def _clamp(score: float, lo: float = 0.0, hi: float = 100.0) -> float:
        return max(lo, min(hi, score))

    def _validate_config(self) -> None:
        """Fail fast on a malformed config (governance / model-risk guardrail)."""
        dim_names = {d.name for d in self.config.dimensions}
        orphaned = [r.id for r in self.config.rules if r.dimension not in dim_names]
        if orphaned:
            raise ValueError(
                f"Config '{self.config.name}' has rules referencing unknown "
                f"dimensions: {orphaned}"
            )
        empty = [
            d.name
            for d in self.config.dimensions
            if not any(r.dimension == d.name for r in self.config.rules)
        ]
        if empty:
            logger.warning(
                "Config '%s' has dimensions with no rules: %s",
                self.config.name,
                empty,
            )


def evaluate(config: AssessmentConfig, inputs: Dict[str, float]) -> AssessmentResult:
    """Convenience one-shot: ``evaluate(config, inputs)``."""
    return AssessmentEngine(config).evaluate(inputs)
