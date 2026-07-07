"""
The mobility composer must be honest: HELM has no live ride-booking integration,
so a "booking" must never fabricate a driver, plate, or claim a real reservation.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from orchestration.response import ResponseComposer
from mobility.executor import build_ride_deeplinks

_DL = {
    "uber": "https://m.uber.com/ul/?action=setPickup&dropoff%5Bnickname%5D=Yoga",
    "maps": "https://www.google.com/maps/dir/?api=1&destination=25.2,55.3",
}


def _booked(label, cost=20, deeplinks=None):
    return ResponseComposer()._format_mobility_response(
        {
            "status": "booked",
            "origin": "current location",
            "destination": "the nearest yoga place",
            "recommended_option": {"label": label, "estimated_cost": cost},
            "booking_details": {
                "driver_name": "Tariq A.",
                "car_model": "Lexus ES300h",
                "license_plate": "D 58291",
                "pickup_eta_mins": 3,
            },
            "deeplinks": deeplinks or {},
        },
        {},
    )


def test_deeplinks_prefill_uber_and_maps():
    dl = build_ride_deeplinks(
        (25.2048, 55.2708), (25.23, 55.30), "Current Location", "Yoga"
    )
    assert dl["uber"].startswith("https://m.uber.com/ul/?")
    assert "setPickup" in dl["uber"] and "dropoff" in dl["uber"]
    assert dl["maps"].startswith("https://www.google.com/maps/dir/")
    # No coordinates → no broken links.
    assert build_ride_deeplinks(None, None, "a", "b") == {}


def test_booking_handoff_includes_real_deeplink():
    text = _booked("Uber / Careem", deeplinks=_DL)
    assert "[Open in Uber →](https://m.uber.com/ul/" in text
    assert "can't place a live ride booking" in text


def test_booking_never_fabricates_a_driver():
    for label in ("Uber X", "Careem GO", "Dubai Taxi (RTA)"):
        text = _booked(label)
        # The mock driver details must not appear as if real.
        assert "Tariq" not in text
        assert "Lexus" not in text
        assert "D 58291" not in text
        assert "Ride Booked" not in text
        # It is transparent that this is not a live booking.
        assert "can't place a live ride booking" in text


def test_booking_hands_off_to_the_right_app():
    assert "Uber" in _booked("Uber X")
    assert "Careem" in _booked("Careem GO")


def test_drive_yourself_is_not_a_booking():
    text = _booked("Drive Yourself", cost=1)
    assert "driving yourself" in text
    assert "estimated fare" not in text.lower()  # no bogus fare for self-drive
    assert "pickup" not in text.lower()
