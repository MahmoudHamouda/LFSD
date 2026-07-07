"""
Regression tests for the orchestrator's mobility signal guard.

A wellbeing question like "Should I go out to run, walk or do some yoga?"
must NOT be treated as a ride request (it previously matched "go" + "to" and
returned ride options with "run" as the destination). Explicit ride requests
must still route to MOBILITY.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from orchestration.intent import IntentClassifier


def _clf():
    return IntentClassifier()


# --- Activity/wellbeing phrasing is NOT mobility ---


def test_run_walk_yoga_is_not_mobility():
    clf = _clf()
    assert (
        clf._has_mobility_signal("Should i go out to run, walk or do some yoga?")
        is False
    )
    assert (
        clf.classify("Should i go out to run, walk or do some yoga?").name != "MOBILITY"
    )


def test_go_for_a_walk_is_not_mobility():
    assert _clf()._has_mobility_signal("go for a walk") is False


def test_go_to_the_gym_is_not_mobility():
    assert _clf()._has_mobility_signal("should I go to the gym") is False


def test_book_a_yoga_class_is_not_mobility():
    # "book" is a mobility keyword but a yoga class is not a ride.
    assert _clf()._has_mobility_signal("book a yoga class") is False


# --- Explicit ride requests are STILL mobility ---


def test_uber_to_airport_is_mobility():
    assert _clf()._has_mobility_signal("book an uber to the airport") is True


def test_ride_to_mall_is_mobility():
    assert _clf()._has_mobility_signal("I need a ride to Dubai Mall") is True


def test_taxi_to_hotel_is_mobility():
    assert _clf()._has_mobility_signal("take a taxi to the hotel") is True


def test_plain_go_to_airport_still_mobility():
    # No activity word, real destination keyword — still a ride.
    assert _clf()._has_mobility_signal("go to the airport") is True
