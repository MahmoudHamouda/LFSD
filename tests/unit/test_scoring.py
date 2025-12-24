import pytest

def test_onboarding_scores(client):
    """Test the onboarding scores endpoint using TestClient."""
    url = "/api/scores/onboarding"
    
    payload = {
        "monthly_income": 5000,
        "monthly_expenses": 3000,
        "total_savings": 10000,
        "total_debt": 0,
        "monthly_debt_payments": 0,
        "is_manual_mode": True,
        "activity_level": "Moderate",
        "sleep_hours": "7-8",
        "diet_style": "Balanced",
        "work_hours_per_week": "40",
        "services_usage": 2
    }

    response = client.post(url, json=payload)
    assert response.status_code in [200, 201]
    data = response.json()
    assert "overall_score" in data or "financial_score" in data # Adjust based on actual response schema
