import unittest
import requests

BASE_URL = "http://localhost:5000"

class TestApiGatewayIntegration(unittest.TestCase):
    def test_user_service_connection(self):
        response = requests.get(f"{BASE_URL}/users/1")
        self.assertEqual(response.status_code, 200)
        self.assertIn("data", response.json())

    def test_financial_service_connection(self):
        response = requests.post(f"{BASE_URL}/users/1/financials/affordability", json={
            "item": "car",
            "price": 30000,
            "loan_term": 60,
            "down_payment": 5000
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("data", response.json())

if __name__ == "__main__":
    unittest.main()
