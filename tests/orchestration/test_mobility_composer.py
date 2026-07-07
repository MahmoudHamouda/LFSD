"""
The mobility composer must be honest: HELM has no live ride-booking integration,
so a "booking" must never fabricate a driver, plate, or claim a real reservation.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from orchestration.response import ResponseComposer


def _booked(label, cost=20):
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
        },
        {},
    )


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
