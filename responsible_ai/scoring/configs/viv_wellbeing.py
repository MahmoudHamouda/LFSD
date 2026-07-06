"""
Reference config: the HELM "Viv" wellbeing score, expressed as an AssessmentConfig.

This demonstrates the thesis of bridge #1: the consumer-facing Viv/HELM score is
just *one configuration* of the generalized AssessmentEngine. The wealth
dimension mirrors the eight pillars of the original ``financial_scoring.py``
(cash-flow stability, bills coverage, discretionary control, savings rate,
emergency buffer, debt load, net-worth momentum, investment health); health and
time are represented with headline rules.

An institution deploying the framework can keep this config, edit it, or ignore
it entirely and supply their own (see ``inclusion_readiness.py``).
"""

from __future__ import annotations

from ..schema import AssessmentConfig, Band, Dimension, Rule


VIV_WELLBEING_CONFIG = AssessmentConfig(
    name="Viv Wellbeing Score",
    version="1.0.0",
    owner="HELM platform",
    description=(
        "Composite personal wellbeing score across Wealth, Health, and Time. "
        "Reference configuration showing the AssessmentEngine reproducing the "
        "original HELM/VivIndex behaviour from declarative policy."
    ),
    changelog=["1.0.0 — initial extraction from financial/health/time scoring."],
    dimensions=[
        Dimension(name="Wealth", weight=1.0, description="Financial wellbeing."),
        Dimension(name="Health", weight=1.0, description="Physical wellbeing."),
        Dimension(name="Time", weight=1.0, description="Time & productivity."),
    ],
    rules=[
        # -- Wealth (mirrors the 8 financial_scoring pillars) --------------
        Rule(
            id="cashflow_stability",
            dimension="Wealth",
            metric="savings_rate",  # net savings / income
            description="Monthly income reliably exceeds expenses.",
            weight=1.5,
            bands=[
                Band(
                    max_value=0.0,
                    score=10,
                    reasoning="Spending exceeds income — negative cash flow.",
                ),
                Band(
                    max_value=0.1,
                    score=55,
                    reasoning="Thin positive cash flow (<10% saved).",
                ),
                Band(
                    max_value=0.2,
                    score=80,
                    reasoning="Healthy cash flow (10-20% saved).",
                ),
                Band(
                    max_value=None,
                    score=100,
                    reasoning="Strong cash flow (>20% saved).",
                ),
            ],
        ),
        Rule(
            id="emergency_buffer",
            dimension="Wealth",
            metric="emergency_fund_months",
            description="Months of expenses held as liquid buffer.",
            weight=1.5,
            bands=[
                Band(
                    max_value=1,
                    score=20,
                    reasoning="< 1 month of buffer — high fragility.",
                ),
                Band(
                    max_value=3, score=60, reasoning="1-3 months of buffer — fragile."
                ),
                Band(
                    max_value=6, score=85, reasoning="3-6 months of buffer — resilient."
                ),
                Band(
                    max_value=None,
                    score=100,
                    reasoning="6+ months of buffer — very resilient.",
                ),
            ],
        ),
        Rule(
            id="debt_load",
            dimension="Wealth",
            metric="debt_to_income",
            description="Debt-service burden relative to income (lower is better).",
            weight=1.2,
            regulatory_ref="Affordability signal",
            bands=[
                Band(
                    max_value=0.2, score=100, reasoning="Low debt burden (DTI <= 20%)."
                ),
                Band(
                    max_value=0.36,
                    score=75,
                    reasoning="Moderate debt burden (DTI 20-36%).",
                ),
                Band(
                    max_value=0.5,
                    score=40,
                    reasoning="Elevated debt burden (DTI 36-50%).",
                ),
                Band(
                    max_value=None, score=15, reasoning="High debt burden (DTI > 50%)."
                ),
            ],
        ),
        Rule(
            id="investment_health",
            dimension="Wealth",
            metric="invested_ratio",  # invested assets / net worth
            description="Long-term asset building relative to net worth.",
            weight=0.8,
            bands=[
                Band(
                    max_value=0.0, score=30, reasoning="No long-term investments yet."
                ),
                Band(
                    max_value=0.2,
                    score=65,
                    reasoning="Beginning to build long-term assets.",
                ),
                Band(
                    max_value=None,
                    score=100,
                    reasoning="Meaningful long-term asset base.",
                ),
            ],
        ),
        # -- Health (headline rules) --------------------------------------
        Rule(
            id="activity",
            dimension="Health",
            metric="weekly_active_minutes",
            description="Weekly active minutes vs. the 150-minute guideline.",
            weight=1.0,
            bands=[
                Band(
                    max_value=60, score=35, reasoning="Well below activity guideline."
                ),
                Band(
                    max_value=150, score=70, reasoning="Approaching activity guideline."
                ),
                Band(
                    max_value=None,
                    score=100,
                    reasoning="Meets/exceeds activity guideline.",
                ),
            ],
        ),
        Rule(
            id="sleep",
            dimension="Health",
            metric="avg_sleep_hours",
            description="Average nightly sleep duration.",
            weight=1.0,
            bands=[
                Band(max_value=5, score=30, reasoning="Chronic short sleep (<5h)."),
                Band(max_value=7, score=70, reasoning="Slightly short sleep (5-7h)."),
                Band(max_value=9, score=100, reasoning="Healthy sleep (7-9h)."),
                Band(max_value=None, score=75, reasoning="Long sleep (>9h) — monitor."),
            ],
        ),
        # -- Time ----------------------------------------------------------
        Rule(
            id="focus",
            dimension="Time",
            metric="focus_ratio",  # focused hours / working hours
            description="Share of working time spent in focused work.",
            weight=1.0,
            bands=[
                Band(max_value=0.2, score=35, reasoning="Highly fragmented time."),
                Band(max_value=0.5, score=70, reasoning="Moderate focus."),
                Band(max_value=None, score=100, reasoning="Strong sustained focus."),
            ],
        ),
    ],
)
