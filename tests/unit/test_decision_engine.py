"""
Tests for the deterministic Decision Engine.

Every decision (binary or multi-option) is scored on Wealth / Health / Time and
grounded in the user's memory (finances, recurring commitments, goals).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from services.intelligence import decision_engine as de
from services.intelligence.schemas import (
    ContextFrame,
    FinancialSnapshot,
    HealthBaseline,
    HelmScores,
)


def _ctx(
    *,
    w=60,
    h=60,
    t=60,
    stress=40,
    act=60,
    hrv=55,
    bal=0,
    sav=0,
    goals=None,
    commit=None,
):
    return ContextFrame(
        user_id="u1",
        user_name="Super",
        helm_scores=HelmScores(wealth=w, health=h, time=t),
        health=HealthBaseline(stress_level=stress, activity_level=act, hrv_avg=hrv),
        financial=FinancialSnapshot(
            total_balance=bal, monthly_savings=sav, currency="AED"
        ),
        life_goals=goals or [],
        commitments=commit or [],
    )


# --- Detection ---------------------------------------------------------------


def test_non_decision_returns_none():
    assert de.evaluate("what is my balance?", _ctx()) is None
    assert de.evaluate("hi there", _ctx()) is None


def test_detects_should_i_and_purchase():
    assert de.looks_like_decision("should i go for a run?")
    assert de.looks_like_decision("I want to buy a car")
    assert de.looks_like_decision("can I afford a laptop?")
    assert not de.looks_like_decision("show me my steps")


# --- Exercise (multi + binary) ----------------------------------------------


def test_multi_activity_stressed_recommends_yoga():
    r = de.evaluate("should i run, walk or do yoga?", _ctx(stress=80))
    assert r.family == "exercise"
    assert r.recommended_key == "yoga"


def test_multi_activity_time_poor_prefers_shorter():
    r = de.evaluate("run or yoga?", _ctx(t=25, stress=30))
    assert r.recommended_key == "run"  # 30-min run beats 45-min yoga


def test_binary_run_adds_rest_option_and_protects_low_recovery():
    c = _ctx(hrv=30)
    r = de.evaluate("should i go for a run?", c)
    keys = {o.key for o in r.options}
    assert keys == {"run", "rest"}
    assert r.recommended_key == "rest"  # low recovery → rest wins


def test_exercise_render_shows_all_three_dimensions():
    c = _ctx(stress=80)
    text = de.render(de.evaluate("run, walk or yoga?", c), c)
    assert "Wealth" in text and "Health" in text and "Time" in text
    assert "My pick:" in text


# --- Purchase (car) ----------------------------------------------------------


def test_car_unknown_price_withholds_pick_and_asks():
    r = de.evaluate("should i buy a car?", _ctx())
    assert r.family == "purchase"
    assert r.recommended_key == ""  # no forced pick without a price
    assert r.followup and "price" in r.followup.lower()


def test_car_affordable_and_time_poor_recommends_buy():
    c = _ctx(bal=80000, sav=3000, w=65, t=35)
    r = de.evaluate("should i buy a car?", c)
    assert r.recommended_key == "buy"


def test_car_unaffordable_recommends_hold_off():
    # savings <= 0 → afford False; low wealth adds pressure.
    c = _ctx(bal=500, sav=0, w=35)
    r = de.evaluate("should i buy a car?", c)
    assert r.recommended_key == "dont"


def test_purchase_surfaces_memory_commitment_and_goal():
    c = _ctx(
        bal=80000,
        sav=3000,
        commit=[{"name": "Careem Plus", "amount": 49, "cadence": "monthly"}],
        goals=[{"title": "New Apartment", "pillar": "finance"}],
    )
    text = de.render(de.evaluate("should i buy a car?", c), c)
    assert "Careem Plus" in text  # existing commitment surfaced
    assert "New Apartment" in text  # goal surfaced
    assert "From your records" in text


# --- General fallback --------------------------------------------------------


def test_general_decision_is_honest_and_asks():
    r = de.evaluate("should i take a pottery class?", _ctx())
    assert r.family == "general"
    assert r.recommended_key == ""  # no fabricated pick
    assert r.followup is not None
    text = de.render(r, _ctx())
    assert "Wealth" in text and "Health" in text and "Time" in text
