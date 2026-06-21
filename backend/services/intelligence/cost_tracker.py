"""
Cost Tracker — Per-Request Token Accounting and Budget Enforcement.

Accumulates token usage across pipeline stages, enforces per-tier hard limits,
and computes estimated cost in USD.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, Optional

from .tier_router import TierRouter

logger = logging.getLogger("intelligence.cost_tracker")


@dataclass
class CostSummary:
    """Immutable summary of pipeline cost for a single request."""

    tier: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    budget_input_remaining: int = 0
    budget_output_remaining: int = 0
    budget_exceeded: bool = False
    stages: Dict[str, Dict[str, int]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "tier": self.tier,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_tokens,
            "estimated_cost_usd": self.estimated_cost_usd,
            "budget_exceeded": self.budget_exceeded,
            "stages": self.stages,
        }


class CostTracker:
    """
    Tracks token costs across a single pipeline execution.

    Create one per request. Accumulate via record_usage().
    Check can_spend() before making LLM calls.
    Finalize via summarize().
    """

    def __init__(self, tier: int, tier_router: TierRouter):
        self.tier = tier
        self.tier_router = tier_router
        self._config = tier_router.get_config(tier)
        self._input_tokens: int = 0
        self._output_tokens: int = 0
        self._stages: Dict[str, Dict[str, int]] = {}

    def can_spend(self, estimated_input: int, estimated_output: int = 0) -> bool:
        """
        Check if a planned LLM call fits within the tier budget.

        Returns False if adding these tokens would exceed limits.
        Should be called BEFORE making an LLM call — if False, skip the call.
        """
        if not self._config.allow_llm:
            return False

        return (
            self._input_tokens + estimated_input
        ) <= self._config.max_input_tokens and (
            self._output_tokens + estimated_output
        ) <= self._config.max_output_tokens

    def record_usage(
        self,
        stage_name: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> None:
        """Record token usage for a pipeline stage."""
        self._input_tokens += input_tokens
        self._output_tokens += output_tokens
        self._stages[stage_name] = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }
        logger.debug(
            "Cost recorded: stage=%s, in=%d, out=%d, total_in=%d, total_out=%d",
            stage_name,
            input_tokens,
            output_tokens,
            self._input_tokens,
            self._output_tokens,
        )

    def summarize(self) -> CostSummary:
        """Produce final cost summary for inclusion in PipelineTrace."""
        cost = self.tier_router.estimate_cost(
            self.tier, self._input_tokens, self._output_tokens
        )
        return CostSummary(
            tier=self.tier,
            total_input_tokens=self._input_tokens,
            total_output_tokens=self._output_tokens,
            total_tokens=self._input_tokens + self._output_tokens,
            estimated_cost_usd=cost,
            budget_input_remaining=max(
                0, self._config.max_input_tokens - self._input_tokens
            ),
            budget_output_remaining=max(
                0, self._config.max_output_tokens - self._output_tokens
            ),
            budget_exceeded=(
                self._input_tokens > self._config.max_input_tokens
                or self._output_tokens > self._config.max_output_tokens
            ),
            stages=dict(self._stages),
        )

    @property
    def total_tokens(self) -> int:
        return self._input_tokens + self._output_tokens
