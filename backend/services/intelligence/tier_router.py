"""
Tier Router — Model Factory with Per-Tier Token Budgets.

Provides tier-aware model selection for the HELM pipeline:
    - Tier 0: No LLM (deterministic only)
    - Tier 1-2: Lightweight model (Gemini Flash)
    - Tier 3: Heavy reasoning model (Gemini Pro)

Token budgets are hard limits — LLM call is skipped if budget exceeded.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from .schemas import RequestTier

logger = logging.getLogger("intelligence.tier_router")


@dataclass(frozen=True)
class TierConfig:
    """Configuration for a single tier."""
    tier: RequestTier
    model_name: str
    max_input_tokens: int
    max_output_tokens: int
    allow_llm: bool
    estimated_cost_per_1k_input: float  # USD per 1K input tokens
    estimated_cost_per_1k_output: float  # USD per 1K output tokens


# Default tier configurations
DEFAULT_TIER_CONFIGS: Dict[int, TierConfig] = {
    0: TierConfig(
        tier=RequestTier.TIER_0,
        model_name="none",
        max_input_tokens=0,
        max_output_tokens=0,
        allow_llm=False,
        estimated_cost_per_1k_input=0.0,
        estimated_cost_per_1k_output=0.0,
    ),
    1: TierConfig(
        tier=RequestTier.TIER_1,
        model_name="light",
        max_input_tokens=400,
        max_output_tokens=100,
        allow_llm=True,
        estimated_cost_per_1k_input=0.00001,   # Flash pricing
        estimated_cost_per_1k_output=0.00004,
    ),
    2: TierConfig(
        tier=RequestTier.TIER_2,
        model_name="light",
        max_input_tokens=800,
        max_output_tokens=200,
        allow_llm=True,
        estimated_cost_per_1k_input=0.00001,
        estimated_cost_per_1k_output=0.00004,
    ),
    3: TierConfig(
        tier=RequestTier.TIER_3,
        model_name="heavy",
        max_input_tokens=2000,
        max_output_tokens=1000,
        allow_llm=True,
        estimated_cost_per_1k_input=0.0005,    # Pro pricing
        estimated_cost_per_1k_output=0.0015,
    ),
}


class TierRouter:
    """
    Tier-aware model factory for the HELM pipeline.

    Provides the correct LLM model instance for each request tier
    and enforces token budgets.
    """

    def __init__(
        self,
        light_model=None,
        heavy_model=None,
        api_key: Optional[str] = None,
        tier_configs: Optional[Dict[int, TierConfig]] = None,
    ):
        """
        Args:
            light_model: Pre-configured lightweight LLM (Gemini Flash).
            heavy_model: Pre-configured heavy LLM (Gemini Pro).
            api_key: API key (for mock detection).
            tier_configs: Override default tier configurations.
        """
        self.light_model = light_model
        self.heavy_model = heavy_model or light_model
        self.api_key = api_key
        self.tier_configs = tier_configs or DEFAULT_TIER_CONFIGS

    def get_model_for_tier(self, tier: int):
        """
        Get the appropriate model for a given tier.

        Returns None for Tier 0 (no LLM needed).
        """
        config = self.tier_configs.get(tier, self.tier_configs[1])

        if not config.allow_llm:
            return None

        if self.api_key == "mock":
            return None

        if config.model_name == "heavy":
            return self.heavy_model
        return self.light_model

    def get_config(self, tier: int) -> TierConfig:
        """Get tier configuration."""
        return self.tier_configs.get(tier, self.tier_configs[1])

    def is_within_budget(self, tier: int, input_tokens: int, output_tokens: int) -> bool:
        """Check if token usage is within tier budget."""
        config = self.get_config(tier)
        return (
            input_tokens <= config.max_input_tokens
            and output_tokens <= config.max_output_tokens
        )

    def estimate_cost(self, tier: int, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost in USD for given token usage at a tier."""
        config = self.get_config(tier)
        cost = (
            (input_tokens / 1000) * config.estimated_cost_per_1k_input
            + (output_tokens / 1000) * config.estimated_cost_per_1k_output
        )
        return round(cost, 6)

    @property
    def is_mock(self) -> bool:
        return self.api_key == "mock"
