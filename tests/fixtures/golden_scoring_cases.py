"""
Golden Test Fixtures for Scoring Policies.

Each entry maps an intent + context setup → expected score deltas + response archetype.
These function as "financial model" regression tests — if any policy change
breaks an existing golden case, the test fails immediately.

Format:
    GOLDEN_CASES = [
        {
            "id": "unique_case_id",
            "intent": "intent_name",
            "entities": {...},
            "context_overrides": {...},
            "expected_wealth_delta": float,
            "expected_health_delta": float,
            "expected_time_delta": float,
            "expected_net_impact": "positive"|"negative"|"neutral"|"mixed",
            "expected_tradeoff": bool,
            "response_archetype": "template_id or description",
        },
        ...
    ]
"""

GOLDEN_CASES = [
    # =====================================================================
    # Wealth Intents
    # =====================================================================
    {
        "id": "GC-W-001",
        "intent": "balance_check",
        "entities": {},
        "context_overrides": {},
        "expected_wealth_delta": 0.0,
        "expected_health_delta": 0.0,
        "expected_time_delta": 0.0,
        "expected_net_impact": "neutral",
        "expected_tradeoff": False,
        "response_archetype": "balance_report",
    },
    {
        "id": "GC-W-002",
        "intent": "spending_report",
        "entities": {},
        "context_overrides": {},
        "expected_wealth_delta": 1.0,
        "expected_health_delta": 0.0,
        "expected_time_delta": 0.0,
        "expected_net_impact": "positive",
        "expected_tradeoff": False,
        "response_archetype": "spending_report",
    },
    {
        "id": "GC-W-003",
        "intent": "financial_advisory",
        "entities": {"amount": 500},
        "context_overrides": {"financial": {"monthly_income": 5000}},
        "expected_wealth_delta": -2.0,
        "expected_health_delta": 0.0,
        "expected_time_delta": 0.0,
        "expected_net_impact": "negative",
        "expected_tradeoff": False,
        "response_archetype": "financial_advice",
    },
    {
        "id": "GC-W-004",
        "intent": "financial_advisory",
        "entities": {"amount": 3000},
        "context_overrides": {"financial": {"monthly_income": 5000}},
        "expected_wealth_delta": -15.0,
        "expected_health_delta": 0.0,
        "expected_time_delta": 0.0,
        "expected_net_impact": "negative",
        "expected_tradeoff": False,
        "response_archetype": "financial_advice",
    },
    {
        "id": "GC-W-005",
        "intent": "set_savings_goal",
        "entities": {"target_amount": 10000},
        "context_overrides": {},
        "expected_wealth_delta": 5.0,
        "expected_health_delta": 0.0,
        "expected_time_delta": 0.0,
        "expected_net_impact": "positive",
        "expected_tradeoff": False,
        "response_archetype": "goal_created",
    },
    {
        "id": "GC-W-006",
        "intent": "bill_payment",
        "entities": {},
        "context_overrides": {},
        "expected_wealth_delta": 2.0,
        "expected_health_delta": 0.0,
        "expected_time_delta": 1.0,
        "expected_net_impact": "positive",
        "expected_tradeoff": False,
        "response_archetype": "bill_payment_confirm",
    },
    {
        "id": "GC-W-007",
        "intent": "subscription_review",
        "entities": {},
        "context_overrides": {"financial": {"monthly_expenses": 4000, "monthly_income": 5000}},
        "expected_wealth_delta": 4.0,
        "expected_health_delta": 0.0,
        "expected_time_delta": 0.0,
        "expected_net_impact": "positive",
        "expected_tradeoff": False,
        "response_archetype": "subscription_list",
    },

    # =====================================================================
    # Health Intents
    # =====================================================================
    {
        "id": "GC-H-001",
        "intent": "sleep_analysis",
        "entities": {},
        "context_overrides": {"health": {"sleep_quality": 35}},
        "expected_wealth_delta": 0.0,
        "expected_health_delta": 5.0,
        "expected_time_delta": 0.0,
        "expected_net_impact": "positive",
        "expected_tradeoff": False,
        "response_archetype": "sleep_report",
    },
    {
        "id": "GC-H-002",
        "intent": "workout_plan",
        "entities": {},
        "context_overrides": {"health": {"activity_level": 25}},
        "expected_wealth_delta": 0.0,
        "expected_health_delta": 8.0,
        "expected_time_delta": -2.0,
        "expected_net_impact": "mixed",
        "expected_tradeoff": True,
        "response_archetype": "workout_plan",
    },
    {
        "id": "GC-H-003",
        "intent": "hydration_reminder",
        "entities": {},
        "context_overrides": {"health": {"activity_level": 70}},
        "expected_wealth_delta": 0.0,
        "expected_health_delta": 3.0,
        "expected_time_delta": 0.0,
        "expected_net_impact": "positive",
        "expected_tradeoff": False,
        "response_archetype": "hydration_reminder",
    },

    # =====================================================================
    # Time Intents
    # =====================================================================
    {
        "id": "GC-T-001",
        "intent": "focus_time_block",
        "entities": {},
        "context_overrides": {},
        "expected_wealth_delta": 0.0,
        "expected_health_delta": 2.0,
        "expected_time_delta": 5.0,
        "expected_net_impact": "positive",
        "expected_tradeoff": False,
        "response_archetype": "focus_time_blocked",
    },
    {
        "id": "GC-T-002",
        "intent": "deadline_reminder",
        "entities": {},
        "context_overrides": {"time": {"productivity_score": 35}},
        "expected_wealth_delta": 0.0,
        "expected_health_delta": 0.0,
        "expected_time_delta": 5.0,
        "expected_net_impact": "positive",
        "expected_tradeoff": False,
        "response_archetype": "reminder_set",
    },
    {
        "id": "GC-T-003",
        "intent": "meeting_schedule",
        "entities": {},
        "context_overrides": {},
        "expected_wealth_delta": 0.0,
        "expected_health_delta": 0.0,
        "expected_time_delta": -1.0,
        "expected_net_impact": "negative",
        "expected_tradeoff": False,
        "response_archetype": "meeting_scheduled",
    },

    # =====================================================================
    # Mobility Intents (Tradeoffs)
    # =====================================================================
    {
        "id": "GC-M-001",
        "intent": "mobility_booking",
        "entities": {},
        "context_overrides": {},
        "expected_wealth_delta": -3.0,
        "expected_health_delta": 0.0,
        "expected_time_delta": 3.0,
        "expected_net_impact": "mixed",
        "expected_tradeoff": True,
        "response_archetype": "ride_booked",
    },
    {
        "id": "GC-M-002",
        "intent": "car_purchase",
        "entities": {},
        "context_overrides": {
            "financial": {"total_balance": 50000, "monthly_income": 8000, "emergency_fund_months": 4},
            "time": {"commute_minutes": 45},
        },
        "expected_wealth_delta": -5.0,
        "expected_health_delta": 0.0,
        "expected_time_delta": 4.0,
        "expected_net_impact": "mixed",
        "expected_tradeoff": True,
        "response_archetype": "car_purchase_analysis",
    },

    # =====================================================================
    # Cross-Domain (Neutral / Passthrough)
    # =====================================================================
    {
        "id": "GC-X-001",
        "intent": "greeting",
        "entities": {},
        "context_overrides": {},
        "expected_wealth_delta": 0.0,
        "expected_health_delta": 0.0,
        "expected_time_delta": 0.0,
        "expected_net_impact": "neutral",
        "expected_tradeoff": False,
        "response_archetype": "greeting",
    },
]
