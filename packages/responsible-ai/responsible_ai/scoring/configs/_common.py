"""Shared helpers for authoring readiness configs concisely."""

from __future__ import annotations

from typing import Optional

from ..schema import Band, Rule


def maturity_bands(absent: str, partial: str, ready: str):
    """Standard 0 / 0.5 / 1.0 maturity bands for a readiness question."""
    return [
        Band(max_value=0.0, score=0, reasoning=absent),
        Band(max_value=0.5, score=50, reasoning=partial),
        Band(max_value=None, score=100, reasoning=ready),
    ]


def question(
    id: str,
    dimension: str,
    metric: str,
    description: str,
    absent: str,
    partial: str,
    ready: str,
    weight: float = 1.0,
    regulatory_ref: Optional[str] = None,
) -> Rule:
    """A readiness question scored on the 0 / 0.5 / 1.0 maturity scale."""
    return Rule(
        id=id,
        dimension=dimension,
        metric=metric,
        description=description,
        weight=weight,
        regulatory_ref=regulatory_ref,
        bands=maturity_bands(absent, partial, ready),
    )
