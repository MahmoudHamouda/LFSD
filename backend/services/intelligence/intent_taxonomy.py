"""
HELM Intent Taxonomy — ~60 Intent Types across Wealth, Health, Time, and Cross-Domain.

Each intent entry specifies:
    - dimensions: which HELM pillars are implicated
    - default_tier: cost tier for LLM routing (0 = deterministic, 3 = heavy reasoning)
    - patterns: regex/keyword patterns for deterministic classification
    - required_entities: what to extract from user input
    - scoring_policy: name of the ScoringPolicy to apply

Design Principle: Deterministic before probabilistic — if a pattern matches,
the LLM is never called.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Pattern


@dataclass(frozen=True)
class IntentEntry:
    """Definition of a single intent type."""
    name: str
    category: str  # "wealth", "health", "time", "mobility", "cross_domain"
    dimensions: tuple  # Affected HELM dimensions
    default_tier: int  # 0–3
    keywords: tuple = ()  # Simple keyword matches (any match triggers)
    regex_patterns: tuple = ()  # Compiled regex patterns (any match triggers)
    required_entities: tuple = ()  # Entities to extract
    scoring_policy: str = ""  # Name of ScoringPolicy in the score engine
    description: str = ""


# ============================================================================
# Wealth Intents
# ============================================================================

WEALTH_INTENTS = [
    IntentEntry(
        name="balance_check",
        category="wealth",
        dimensions=("wealth",),
        default_tier=0,
        keywords=("what is my balance", "check balance", "account balance",
                  "how much do i have", "total balance", "bank balance"),
        description="Check account balance(s).",
    ),
    IntentEntry(
        name="spending_report",
        category="wealth",
        dimensions=("wealth",),
        default_tier=0,
        keywords=("how much did i spend", "spending report", "my spending",
                  "what did i spend on", "spending breakdown", "expense report",
                  "how much have i spent", "show my expenses"),
        required_entities=("time_period", "category"),
        scoring_policy="spending_report",
        description="Retrieve spending data with optional category/period filters.",
    ),
    IntentEntry(
        name="financial_advisory",
        category="wealth",
        dimensions=("wealth",),
        default_tier=2,
        keywords=("can i afford", "should i buy", "is it worth",
                  "financial advice", "money advice", "afford this"),
        regex_patterns=(r"can i (?:afford|buy|spend)", r"should i (?:buy|invest|spend)"),
        required_entities=("amount", "item"),
        scoring_policy="financial_advisory",
        description="Feasibility questions requiring financial analysis.",
    ),
    IntentEntry(
        name="set_savings_goal",
        category="wealth",
        dimensions=("wealth",),
        default_tier=0,
        keywords=("save to plan", "add to goals", "set a goal", "savings goal",
                  "set goal", "save for", "saving for"),
        regex_patterns=(r"save\s+(?:for|towards?)\s+", r"goal.*\d+"),
        required_entities=("title", "target_amount", "deadline"),
        scoring_policy="goal_set",
        description="Setting a savings or financial goal.",
    ),
    IntentEntry(
        name="bill_payment",
        category="wealth",
        dimensions=("wealth",),
        default_tier=0,
        keywords=("pay my", "pay bill", "pay credit card", "make payment",
                  "settle bill", "clear balance"),
        scoring_policy="bill_payment",
        description="Execute a bill or credit card payment.",
    ),
    IntentEntry(
        name="budget_alert",
        category="wealth",
        dimensions=("wealth",),
        default_tier=0,
        keywords=("budget alert", "over budget", "spending limit",
                  "budget status", "am i over budget"),
        description="Check budget status or set alerts.",
    ),
    IntentEntry(
        name="investment_query",
        category="wealth",
        dimensions=("wealth",),
        default_tier=1,
        keywords=("investment", "portfolio", "stocks", "mutual fund",
                  "where to invest", "investment advice"),
        scoring_policy="investment_query",
        description="Investment-related queries.",
    ),
    IntentEntry(
        name="loan_inquiry",
        category="wealth",
        dimensions=("wealth",),
        default_tier=1,
        keywords=("loan", "borrow", "mortgage", "interest rate",
                  "loan options", "apply for loan"),
        scoring_policy="loan_inquiry",
        description="Loan or mortgage queries.",
    ),
    IntentEntry(
        name="salary_analysis",
        category="wealth",
        dimensions=("wealth",),
        default_tier=0,
        keywords=("my salary", "income analysis", "how much do i earn",
                  "monthly income", "paycheck"),
        description="Salary or income analysis.",
    ),
    IntentEntry(
        name="expense_categorize",
        category="wealth",
        dimensions=("wealth",),
        default_tier=0,
        keywords=("categorize expense", "what category", "recategorize",
                  "expense category"),
        description="Categorize or recategorize expenses.",
    ),
    IntentEntry(
        name="net_worth_check",
        category="wealth",
        dimensions=("wealth",),
        default_tier=0,
        keywords=("net worth", "total assets", "how much am i worth",
                  "asset summary"),
        description="Check net worth or asset summary.",
    ),
    IntentEntry(
        name="cashflow_report",
        category="wealth",
        dimensions=("wealth",),
        default_tier=0,
        keywords=("cashflow", "cash flow", "money in and out",
                  "income vs expenses", "money flow"),
        scoring_policy="cashflow_report",
        description="Income vs. expenses cashflow report.",
    ),
    IntentEntry(
        name="subscription_review",
        category="wealth",
        dimensions=("wealth",),
        default_tier=0,
        keywords=("subscriptions", "recurring charges", "cancel subscription",
                  "subscription review", "what am i subscribed to"),
        description="Review or manage recurring subscriptions.",
    ),
]


# ============================================================================
# Health Intents
# ============================================================================

HEALTH_INTENTS = [
    IntentEntry(
        name="health_report",
        category="health",
        dimensions=("health",),
        default_tier=0,
        keywords=("health report", "health summary", "my health",
                  "health status", "how is my health", "health data"),
        description="General health data retrieval.",
    ),
    IntentEntry(
        name="sleep_analysis",
        category="health",
        dimensions=("health",),
        default_tier=0,
        keywords=("sleep", "how did i sleep", "sleep quality",
                  "sleep score", "sleep data", "insomnia", "rest"),
        scoring_policy="sleep_analysis",
        description="Sleep quality and duration analysis.",
    ),
    IntentEntry(
        name="activity_summary",
        category="health",
        dimensions=("health",),
        default_tier=0,
        keywords=("steps", "activity", "workout summary", "exercise",
                  "how active", "calories burned", "activity level"),
        scoring_policy="activity_summary",
        description="Physical activity and exercise summary.",
    ),
    IntentEntry(
        name="nutrition_log",
        category="health",
        dimensions=("health",),
        default_tier=0,
        keywords=("log food", "nutrition", "what i ate", "meal log",
                  "calories intake", "track food", "diet"),
        scoring_policy="nutrition_log",
        description="Log or query nutrition data.",
    ),
    IntentEntry(
        name="stress_check",
        category="health",
        dimensions=("health",),
        default_tier=0,
        keywords=("stress", "stressed", "anxiety", "mental load",
                  "overwhelmed", "burnout"),
        scoring_policy="stress_check",
        description="Stress level assessment.",
    ),
    IntentEntry(
        name="recovery_status",
        category="health",
        dimensions=("health",),
        default_tier=0,
        keywords=("recovery", "hrv", "readiness", "heart rate variability",
                  "recovery score"),
        scoring_policy="recovery_status",
        description="Recovery and readiness status.",
    ),
    IntentEntry(
        name="workout_plan",
        category="health",
        dimensions=("health", "time"),
        default_tier=1,
        keywords=("workout plan", "exercise plan", "training plan",
                  "gym schedule", "fitness plan"),
        scoring_policy="workout_plan",
        description="Generate or modify workout plans.",
    ),
    IntentEntry(
        name="hydration_reminder",
        category="health",
        dimensions=("health",),
        default_tier=0,
        keywords=("water", "hydration", "drink water", "hydrate"),
        description="Water intake tracking and reminders.",
    ),
    IntentEntry(
        name="mental_health_check",
        category="health",
        dimensions=("health",),
        default_tier=1,
        keywords=("how am i feeling", "mood", "mental health",
                  "emotional state", "feeling down", "feeling good"),
        scoring_policy="mental_health_check",
        description="Emotional and mental health check-in.",
    ),
    IntentEntry(
        name="health_goal_set",
        category="health",
        dimensions=("health",),
        default_tier=0,
        keywords=("health goal", "fitness goal", "run 5k", "lose weight",
                  "gain muscle", "step goal"),
        required_entities=("title", "target", "deadline"),
        scoring_policy="health_goal_set",
        description="Set a health or fitness goal.",
    ),
]


# ============================================================================
# Time & Productivity Intents
# ============================================================================

TIME_INTENTS = [
    IntentEntry(
        name="schedule_event",
        category="time",
        dimensions=("time",),
        default_tier=0,
        keywords=("schedule", "book time", "add to calendar", "save time for",
                  "allocate time", "set reminder", "create event"),
        regex_patterns=(r"(?:schedule|book|allocate).*(?:hours|minutes|tomorrow|week)",),
        required_entities=("title", "time_slot", "duration"),
        scoring_policy="schedule_event",
        description="Create a calendar event or time block.",
    ),
    IntentEntry(
        name="calendar_view",
        category="time",
        dimensions=("time",),
        default_tier=0,
        keywords=("my calendar", "what's on my calendar", "upcoming events",
                  "schedule today", "what's next", "agenda"),
        description="View calendar events.",
    ),
    IntentEntry(
        name="focus_time_block",
        category="time",
        dimensions=("time", "health"),
        default_tier=0,
        keywords=("focus time", "deep work", "do not disturb",
                  "block focus", "concentration time", "no meetings"),
        scoring_policy="focus_time_block",
        description="Block focused work time on calendar.",
    ),
    IntentEntry(
        name="meeting_schedule",
        category="time",
        dimensions=("time",),
        default_tier=1,
        keywords=("schedule meeting", "set up meeting", "book meeting",
                  "team meeting", "call with"),
        required_entities=("attendees", "time_slot", "duration"),
        scoring_policy="meeting_schedule",
        description="Schedule a meeting with other people.",
    ),
    IntentEntry(
        name="deadline_reminder",
        category="time",
        dimensions=("time",),
        default_tier=0,
        keywords=("deadline", "due date", "remind me", "reminder",
                  "don't forget"),
        required_entities=("task", "deadline"),
        description="Set a deadline reminder.",
    ),
    IntentEntry(
        name="time_audit",
        category="time",
        dimensions=("time",),
        default_tier=0,
        keywords=("where does my time go", "time audit", "time report",
                  "time tracking", "how do i spend my time"),
        scoring_policy="time_audit",
        description="Analyze time allocation patterns.",
    ),
    IntentEntry(
        name="productivity_report",
        category="time",
        dimensions=("time",),
        default_tier=0,
        keywords=("productivity", "productivity score", "how productive",
                  "productivity report", "efficiency"),
        description="Productivity metrics and report.",
    ),
    IntentEntry(
        name="commute_planning",
        category="time",
        dimensions=("time", "wealth"),
        default_tier=1,
        keywords=("commute", "best route", "how long to get", "travel time",
                  "directions to", "route to"),
        scoring_policy="commute_planning",
        description="Commute optimization and planning.",
    ),
]


# ============================================================================
# Mobility Intents
# ============================================================================

MOBILITY_INTENTS = [
    IntentEntry(
        name="mobility_price_check",
        category="mobility",
        dimensions=("wealth", "time"),
        default_tier=0,
        keywords=("ride prices", "how much is a ride", "uber price",
                  "careem price", "ride cost", "check ride", "taxi price"),
        required_entities=("destination", "start_location"),
        scoring_policy="mobility_price_check",
        description="Check ride prices from providers.",
    ),
    IntentEntry(
        name="mobility_booking",
        category="mobility",
        dimensions=("wealth", "time"),
        default_tier=0,
        keywords=("book a ride", "book uber", "book careem", "get me a ride",
                  "order a cab", "book taxi", "take me to"),
        regex_patterns=(r"book.*(?:uber|careem|ride|cab|taxi)",
                        r"(?:take|get) me (?:to|a)", r"ride to"),
        required_entities=("destination", "start_location", "provider", "ride_type"),
        scoring_policy="mobility_booking",
        description="Book a ride with a provider.",
    ),
    IntentEntry(
        name="mobility_cancellation",
        category="mobility",
        dimensions=("wealth",),
        default_tier=0,
        keywords=("cancel ride", "cancel booking", "cancel my ride",
                  "cancel uber", "cancel careem"),
        description="Cancel an active ride booking.",
    ),
    IntentEntry(
        name="get_bookings",
        category="mobility",
        dimensions=("time",),
        default_tier=0,
        keywords=("my bookings", "active bookings", "current rides",
                  "ride status", "booking status"),
        description="View active bookings and reservations.",
    ),
    IntentEntry(
        name="car_purchase",
        category="mobility",
        dimensions=("wealth", "time"),
        default_tier=1,
        keywords=("buy a car", "buy car", "new car", "used car",
                  "car options", "installment car", "auto loan", "vehicle"),
        regex_patterns=(r"buy\s+a?\s*(?:new|used)?\s*car",),
        scoring_policy="car_purchase",
        description="Car purchase analysis and recommendations.",
    ),
]


# ============================================================================
# Cross-Domain Intents
# ============================================================================

CROSS_DOMAIN_INTENTS = [
    IntentEntry(
        name="tradeoff_analysis",
        category="cross_domain",
        dimensions=("wealth", "health", "time"),
        default_tier=3,
        keywords=("should i", "compare", "trade off", "tradeoff",
                  "what if", "pros and cons", "which is better",
                  "help me decide", "help me think"),
        regex_patterns=(r"should i .+ or .+", r"(?:which|what) (?:is|would be) better"),
        scoring_policy="tradeoff_analysis",
        description="Multi-dimensional tradeoff analysis requiring deep reasoning.",
    ),
    IntentEntry(
        name="career_change",
        category="cross_domain",
        dimensions=("wealth", "health", "time"),
        default_tier=3,
        keywords=("new job", "career change", "job offer", "switch jobs",
                  "higher pay", "new position", "job opportunity"),
        scoring_policy="career_change",
        description="Career change impact analysis across all dimensions.",
    ),
    IntentEntry(
        name="relocation_analysis",
        category="cross_domain",
        dimensions=("wealth", "health", "time"),
        default_tier=3,
        keywords=("relocate", "move to", "moving abroad", "living in",
                  "cost of living"),
        scoring_policy="relocation_analysis",
        description="Relocation impact analysis.",
    ),
    IntentEntry(
        name="life_event_planning",
        category="cross_domain",
        dimensions=("wealth", "health", "time"),
        default_tier=3,
        keywords=("having a baby", "getting married", "wedding", "retirement",
                  "buying a house", "house purchase"),
        scoring_policy="life_event_planning",
        description="Major life event impact analysis.",
    ),
    IntentEntry(
        name="general_conversation",
        category="cross_domain",
        dimensions=(),
        default_tier=1,
        keywords=(),  # Fallback — no keywords, classified by LLM or default
        description="General conversation, social talk, or non-actionable queries.",
    ),
    IntentEntry(
        name="needs_clarification",
        category="cross_domain",
        dimensions=(),
        default_tier=1,
        keywords=(),  # Never triggered by keywords — only by LLM or ambiguity detection
        description="Input is ambiguous and requires clarification.",
    ),
    IntentEntry(
        name="greeting",
        category="cross_domain",
        dimensions=(),
        default_tier=0,
        keywords=("hello", "hi", "hey", "good morning", "good evening",
                  "good afternoon", "howdy", "what's up", "sup"),
        description="Social greeting.",
    ),
    IntentEntry(
        name="feedback",
        category="cross_domain",
        dimensions=(),
        default_tier=0,
        keywords=("feedback", "suggestion", "complaint", "bug report",
                  "feature request", "this is broken"),
        description="User providing feedback or reporting issues.",
    ),
]


# ============================================================================
# Taxonomy Registry
# ============================================================================

ALL_INTENTS: List[IntentEntry] = (
    WEALTH_INTENTS
    + HEALTH_INTENTS
    + TIME_INTENTS
    + MOBILITY_INTENTS
    + CROSS_DOMAIN_INTENTS
)

# Lookup by name → IntentEntry
INTENT_REGISTRY: Dict[str, IntentEntry] = {entry.name: entry for entry in ALL_INTENTS}

# Compiled regex patterns for deterministic matching (built once at import)
_COMPILED_PATTERNS: List[tuple] = []  # (compiled_pattern, intent_name)

for _entry in ALL_INTENTS:
    for _pattern_str in _entry.regex_patterns:
        _COMPILED_PATTERNS.append((re.compile(_pattern_str, re.IGNORECASE), _entry.name))


def get_intent_entry(intent_name: str) -> Optional[IntentEntry]:
    """Look up an intent definition by name."""
    return INTENT_REGISTRY.get(intent_name)


def get_intents_by_category(category: str) -> List[IntentEntry]:
    """Get all intents in a category."""
    return [e for e in ALL_INTENTS if e.category == category]


def get_all_intent_names() -> List[str]:
    """Get a flat list of all intent names for LLM prompt generation."""
    return [e.name for e in ALL_INTENTS]


def match_deterministic(text: str) -> Optional[tuple]:
    """
    Attempt deterministic intent classification via keywords and regex.

    Returns:
        (intent_name, confidence, match_type) or None if no match.
    """
    text_lower = text.lower().strip()

    # Pass 1: Exact keyword matching (highest confidence)
    for entry in ALL_INTENTS:
        for keyword in entry.keywords:
            if keyword in text_lower:
                return (entry.name, 0.95, "keyword")

    # Pass 2: Regex pattern matching
    for compiled_pattern, intent_name in _COMPILED_PATTERNS:
        if compiled_pattern.search(text_lower):
            return (intent_name, 0.85, "regex")

    return None
