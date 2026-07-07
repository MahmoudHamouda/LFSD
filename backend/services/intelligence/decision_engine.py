"""
Deterministic Decision Engine — every decision, scored on Wealth / Health / Time.

HELM's job on a decision is not to describe the options, it's to *weigh* them.
This engine takes any decision — binary ("should I go for a run?", "should I buy
a car?") or multi-option ("run, walk or yoga?") — enumerates the choices
(including the "don't" baseline for binary decisions), estimates each option's
directional impact on the three HELM dimensions, grounds it in the user's memory
(finances, recurring commitments, goals), and recommends.

Design principles:
    - Deterministic and traceable: the recommendation follows from real signals.
    - Honest: show DIRECTION per dimension (↑/↓/→) with grounded notes; only use
      concrete numbers we actually have (balance, subscription amounts). Never
      fabricate precise costs or times.
    - Memory-aware: check recurring commitments and goals for anything that
      changes the call ("you already pay AED 49/mo for Careem Plus").
    - Extensible: add a family by adding a builder; the framework is shared.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Activity model (shared with the wellbeing family)
# ---------------------------------------------------------------------------

ACTIVITY_PROFILES: Dict[str, Dict[str, Any]] = {
    "run": {
        "label": "Running",
        "time_min": 30,
        "cost": "Free (outdoors)",
        "free": True,
        "cardio": 0.9,
        "strength": 0.3,
        "flexibility": 0.1,
        "stress_relief": 0.5,
        "intensity": 0.9,
        "low_impact": False,
        "best_for": "cardio & endurance",
    },
    "jog": {
        "label": "Jogging",
        "time_min": 30,
        "cost": "Free (outdoors)",
        "free": True,
        "cardio": 0.7,
        "strength": 0.3,
        "flexibility": 0.1,
        "stress_relief": 0.6,
        "intensity": 0.7,
        "low_impact": False,
        "best_for": "a moderate cardio boost",
    },
    "walk": {
        "label": "Walking",
        "time_min": 30,
        "cost": "Free (outdoors)",
        "free": True,
        "cardio": 0.4,
        "strength": 0.2,
        "flexibility": 0.1,
        "stress_relief": 0.8,
        "intensity": 0.3,
        "low_impact": True,
        "best_for": "low-impact movement & de-stressing",
    },
    "yoga": {
        "label": "Yoga",
        "time_min": 45,
        "cost": "Free at home (studio fees vary)",
        "free": True,
        "cardio": 0.2,
        "strength": 0.5,
        "flexibility": 0.9,
        "stress_relief": 0.9,
        "intensity": 0.4,
        "low_impact": True,
        "best_for": "flexibility, strength & calm",
    },
    "swim": {
        "label": "Swimming",
        "time_min": 45,
        "cost": "Pool fee",
        "free": False,
        "cardio": 0.8,
        "strength": 0.6,
        "flexibility": 0.4,
        "stress_relief": 0.6,
        "intensity": 0.7,
        "low_impact": True,
        "best_for": "full-body, low-impact cardio",
    },
    "gym": {
        "label": "Gym workout",
        "time_min": 60,
        "cost": "Membership",
        "free": False,
        "cardio": 0.6,
        "strength": 0.9,
        "flexibility": 0.2,
        "stress_relief": 0.4,
        "intensity": 0.8,
        "low_impact": False,
        "best_for": "building strength",
    },
    "cycle": {
        "label": "Cycling",
        "time_min": 45,
        "cost": "Free (own bike)",
        "free": True,
        "cardio": 0.8,
        "strength": 0.4,
        "flexibility": 0.1,
        "stress_relief": 0.6,
        "intensity": 0.7,
        "low_impact": True,
        "best_for": "low-impact cardio",
    },
}

ACTIVITY_ALIASES: Dict[str, str] = {
    "run": "run",
    "running": "run",
    "jog": "jog",
    "jogging": "jog",
    "walk": "walk",
    "walking": "walk",
    "stroll": "walk",
    "yoga": "yoga",
    "swim": "swim",
    "swimming": "swim",
    "gym": "gym",
    "workout": "gym",
    "cycle": "cycle",
    "cycling": "cycle",
    "bike": "cycle",
    "biking": "cycle",
}

# Arrow glyphs for a dimension's direction.
_ARROWS = {"up": "↑", "down": "↓", "neutral": "→"}


# ---------------------------------------------------------------------------
# Result model
# ---------------------------------------------------------------------------


@dataclass
class DimImpact:
    direction: str = "neutral"  # "up" | "down" | "neutral"
    note: str = ""


@dataclass
class Option:
    key: str
    label: str
    wealth: DimImpact = field(default_factory=DimImpact)
    health: DimImpact = field(default_factory=DimImpact)
    time: DimImpact = field(default_factory=DimImpact)
    suitability: float = 0.0


@dataclass
class DecisionResult:
    family: str
    options: List[Option]
    recommended_key: str
    reason: str
    memory_notes: List[str] = field(default_factory=list)
    followup: Optional[str] = None  # clarifying question (general decisions)


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

_DECISION_RE = re.compile(
    r"\b(should i|shall i|do you think i should|is it worth|worth it|"
    r"i want to buy|i'm thinking of buying|thinking about buying|"
    r"should we|or (?:not|don't)|better to)\b",
    re.IGNORECASE,
)
# Gate for the purchase family — deliberately excludes bare "get" (too common).
_PURCHASE_RE = re.compile(
    r"\b(buy|purchase|afford|subscribe to|sign up for)\b", re.IGNORECASE
)


def looks_like_decision(text: str) -> bool:
    """A quick gate: does this message ask us to weigh a choice?"""
    t = (text or "").lower()
    if _DECISION_RE.search(t):
        return True
    if _PURCHASE_RE.search(t):
        return True
    # "run, walk or yoga?" style comparisons.
    if " or " in t and _detect_activities(t):
        return True
    return False


def _detect_activities(text: str) -> List[str]:
    blob = (text or "").lower()
    hits = []
    for word, key in ACTIVITY_ALIASES.items():
        if re.search(rf"\b{re.escape(word)}\b", blob):
            hits.append((blob.find(word), key))
    seen, ordered = set(), []
    for _, key in sorted(hits):
        if key not in seen:
            seen.add(key)
            ordered.append(key)
    return ordered


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


def evaluate(text: str, context) -> Optional[DecisionResult]:
    """
    Return a DecisionResult for a decision message, or None if this isn't a
    decision we should weigh (caller falls back to normal handling).
    """
    if not looks_like_decision(text):
        return None

    activities = _detect_activities(text)
    if activities:
        return _exercise_decision(text, context, activities)

    if _PURCHASE_RE.search(text.lower()):
        return _purchase_decision(text, context)

    # Generic "should I X?" — we can still frame it honestly on W/H/T.
    return _general_decision(text, context)


# --- Exercise (multi-option or binary "should I run?") ---------------------


def _exercise_decision(text, context, activities: List[str]) -> DecisionResult:
    health_s = context.helm_scores.health
    time_s = context.helm_scores.time
    wealth_s = context.helm_scores.wealth
    stress = context.health.stress_level
    activity = context.health.activity_level
    recovery = context.health.hrv_avg if context.health.hrv_avg else 50.0

    signals = {
        "time_poor": time_s < 50,
        "stressed": stress >= 55,
        "low_activity": activity < 50 or health_s < 50,
        "low_recovery": recovery < 40,
        "wealth_low": wealth_s < 45,
    }

    def suitability(p) -> float:
        s = p["cardio"] * 0.5 + p["strength"] * 0.3 + p["flexibility"] * 0.2
        if signals["low_activity"]:
            s += p["cardio"] * 0.6
        if signals["stressed"]:
            s += p["stress_relief"] * 0.9
        elif stress >= 40:
            s += p["stress_relief"] * 0.4
        if signals["time_poor"]:
            s += (60 - p["time_min"]) / 60 * 0.7
        if signals["low_recovery"]:
            s += 0.5 if p["low_impact"] else -0.3
            s -= p["intensity"] * 0.4
        if signals["wealth_low"] and p["free"]:
            s += 0.3
        return s

    options: List[Option] = []
    for key in activities:
        p = ACTIVITY_PROFILES[key]
        options.append(
            Option(
                key=key,
                label=p["label"],
                health=DimImpact("up", f"builds {p['best_for']}"),
                time=DimImpact("down", f"~{p['time_min']} min"),
                wealth=DimImpact("neutral" if p["free"] else "down", p["cost"]),
                suitability=suitability(p),
            )
        )

    # Binary case: a single activity → add the "rest / not today" baseline.
    if len(activities) == 1:
        rest_good = signals["low_recovery"]
        options.append(
            Option(
                key="rest",
                label="Rest / skip it today",
                health=DimImpact(
                    "up" if rest_good else "down",
                    "protects low recovery" if rest_good else "misses today's benefit",
                ),
                time=DimImpact("up", "keeps the time free"),
                wealth=DimImpact("neutral", "no cost"),
                # Resting only wins when recovery is low or the user is very time-poor.
                suitability=(0.9 if rest_good else 0.0)
                + (0.4 if signals["time_poor"] else 0.0),
            )
        )

    options.sort(key=lambda o: o.suitability, reverse=True)
    winner = options[0]
    reason = _exercise_reason(winner, signals, context)
    memory = _goal_notes(context, pillar="health")
    return DecisionResult("exercise", options, winner.key, reason, memory)


def _exercise_reason(winner: Option, signals, context) -> str:
    if winner.key == "rest":
        if signals["low_recovery"]:
            return (
                f"your recovery is low (HRV {context.health.hrv_avg:.0f}), so a rest "
                "day protects it more than pushing a workout"
            )
        return "you're short on time today, so skipping is the low-cost choice"
    p = ACTIVITY_PROFILES[winner.key]
    bits = []
    if signals["stressed"] and p["stress_relief"] >= 0.7:
        bits.append(
            f"your stress is elevated ({context.health.stress_level:.0f}/100) and "
            f"{p['label'].lower()} is one of the calmest options"
        )
    if signals["time_poor"]:
        bits.append(
            f"you're short on time (Time {context.helm_scores.time:.0f}/100) and it "
            f"fits in ~{p['time_min']} min"
        )
    if signals["low_activity"] and p["cardio"] >= 0.7:
        bits.append("your recent activity is low, so the cardio boost helps most")
    if signals["low_recovery"] and p["low_impact"]:
        bits.append("your recovery is low, so a gentle, low-impact session protects it")
    if not bits:
        bits.append(
            "your Health, Time and Wealth are all in good shape, so this is the best "
            "all-round benefit for the time it takes"
        )
    return "; ".join(bits)


# --- Purchase (car / general purchase, binary buy vs don't) ----------------

_CAR_RE = re.compile(r"\bcar\b|\bvehicle\b|\bauto\b", re.IGNORECASE)


def _purchase_decision(text, context) -> DecisionResult:
    fin = context.financial
    is_car = bool(_CAR_RE.search(text))
    item = "a car" if is_car else _extract_item(text)

    # Affordability from real numbers (memory).
    memory: List[str] = []
    afford = None  # None = unknown
    if fin.total_balance or fin.monthly_savings:
        memory.append(
            f"balance ~{fin.currency} {fin.total_balance:,.0f}, "
            f"saving ~{fin.currency} {fin.monthly_savings:,.0f}/mo"
        )
        # Very rough: comfortable if healthy monthly savings and some balance.
        afford = fin.monthly_savings > 0 and fin.total_balance > 0

    # Commitments memory — does the user already pay for this category?
    for c in context.commitments or []:
        name = (c.get("name") or "").lower()
        if is_car and re.search(r"car|auto|careem|uber|salik|rta|parking|fuel", name):
            memory.append(
                f"you already pay {fin.currency} {c.get('amount'):,.0f}/"
                f"{c.get('cadence','mo')} for {c.get('name')}"
            )

    # Goal conflicts (memory).
    memory += _goal_notes(context, pillar="wealth")

    buy = Option(
        key="buy",
        label=f"Buy {item}",
        wealth=DimImpact(
            "down",
            "a major outlay"
            + (
                ""
                if afford is None
                else (" you can absorb" if afford else " that strains your cash")
            ),
        ),
        time=DimImpact(
            "up" if is_car else "neutral",
            "cuts commute time" if is_car else "depends on the item",
        ),
        health=DimImpact(
            "down" if is_car else "neutral",
            "less incidental walking" if is_car else "",
        ),
        suitability=0.0,
    )
    dont = Option(
        key="dont",
        label=f"Hold off on {item}",
        wealth=DimImpact("up", "keeps your cash and savings intact"),
        time=DimImpact(
            "down" if is_car else "neutral", "commute stays as-is" if is_car else ""
        ),
        health=DimImpact("neutral", ""),
        suitability=0.0,
    )

    # Recommendation: lean on affordability + wealth score + goal pressure.
    wealth_s = context.helm_scores.wealth
    time_s = context.helm_scores.time
    goal_pressure = any("goal" in m for m in memory)
    buy_score, dont_score = 0.0, 0.0
    if afford is True:
        buy_score += 0.6
    if afford is False:
        dont_score += 1.0
    if wealth_s < 45:
        dont_score += 0.6
    if goal_pressure:
        dont_score += 0.5
    if is_car and time_s < 40:  # very time-poor → a car's time saving matters
        buy_score += 0.6
    buy.suitability, dont.suitability = buy_score, dont_score

    options = sorted([buy, dont], key=lambda o: o.suitability, reverse=True)
    winner = options[0]

    # Price unknown → don't force a pick; ask for the number first (honest).
    if afford is None:
        return DecisionResult(
            family="purchase",
            options=options,
            recommended_key="",
            reason=(
                "here's the shape of the trade-off — a car buys back commute time "
                "but it's a real hit to Wealth. To give you a firm yes/no I need the "
                "price to weigh against your balance and goals"
            ),
            memory_notes=memory,
            followup="What's the price (or monthly payment) you're considering?",
        )

    if winner.key == "buy":
        reason = (
            "the time it buys back outweighs the cost given your finances"
            if is_car
            else "it looks affordable and doesn't fight your goals"
        )
    else:
        reasons = []
        if afford is False or wealth_s < 45:
            reasons.append("it would strain your cash right now")
        if goal_pressure:
            reasons.append("it competes with a savings goal you're funding")
        if not reasons:
            reasons.append("the wealth hit outweighs the benefit at the moment")
        reason = "; ".join(reasons)

    return DecisionResult("purchase", options, winner.key, reason, memory, None)


def _extract_item(text: str) -> str:
    m = re.search(
        r"\b(?:buy|purchase|get|afford|subscribe to|sign up for)\s+(?:a|an|the|some)?\s*"
        r"([a-zA-Z][a-zA-Z0-9\s\-]{1,40}?)(?=\?|\.|,|$|\bor\b|\bnow\b|\btoday\b)",
        text.lower(),
    )
    if m:
        return m.group(1).strip() or "it"
    return "it"


# --- General "should I X?" (honest framing + clarifier) --------------------


def _general_decision(text, context) -> DecisionResult:
    do = Option(
        key="do",
        label="Do it",
        wealth=DimImpact("neutral", "depends on the specifics"),
        health=DimImpact("neutral", ""),
        time=DimImpact("neutral", ""),
    )
    dont = Option(key="dont", label="Hold off", suitability=0.0)
    return DecisionResult(
        family="general",
        options=[do, dont],
        recommended_key="",
        reason=(
            "I weigh every choice on your Wealth, Health and Time. To give you a "
            "grounded call on this one, I need a bit more detail"
        ),
        memory_notes=[],
        followup=(
            "What's the main cost or time commitment involved, and what are you "
            "hoping it improves?"
        ),
    )


# --- Shared: goal memory ----------------------------------------------------


def _goal_notes(context, pillar: str) -> List[str]:
    notes = []
    for g in context.life_goals or []:
        if str(g.get("pillar", "")).lower() in (
            pillar,
            "finance" if pillar == "wealth" else pillar,
        ):
            title = g.get("title")
            if title:
                notes.append(f"goal in play: '{title}'")
    return notes[:2]


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def render(result: DecisionResult, context) -> str:
    """Render a decision as grounded markdown: per-option W/H/T + a rec."""
    h = context.helm_scores.health
    t = context.helm_scores.time
    w = context.helm_scores.wealth
    lines = [
        f"Weighing this against your **Wealth {w:.0f} · Health {h:.0f} · Time {t:.0f}**:\n"
    ]
    for o in result.options:
        dims = (
            f"Wealth {_ARROWS[o.wealth.direction]}"
            + (f" ({o.wealth.note})" if o.wealth.note else "")
            + f" · Health {_ARROWS[o.health.direction]}"
            + (f" ({o.health.note})" if o.health.note else "")
            + f" · Time {_ARROWS[o.time.direction]}"
            + (f" ({o.time.note})" if o.time.note else "")
        )
        lines.append(f"- **{o.label}** — {dims}")

    if result.memory_notes:
        # Use *italic* (the chat renderer supports * but not _ emphasis).
        lines.append("\n*From your records: " + "; ".join(result.memory_notes) + ".*")

    if result.recommended_key:
        rec = next((o for o in result.options if o.key == result.recommended_key), None)
        if rec:
            lines.append(f"\n**My pick: {rec.label}.** Because {result.reason}.")
    elif result.reason:
        lines.append(f"\n{result.reason}.")

    if result.followup:
        lines.append(f"\n{result.followup}")

    return "\n".join(lines)
