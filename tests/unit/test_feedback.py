import unittest
from flask import Flask
from services.chat_service.app import app
from services.chat_service.db import init_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class TestFeedbackIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine("sqlite:///:memory:")  # In-memory DB for testing
        cls.Session = sessionmaker(bind=cls.engine)
        init_db(cls.engine)

        cls.app = app
        cls.app.testing = True
        cls.client = cls.app.test_client()

    def test_feedback_submission_and_retrieval(self):
        # Submit feedback
        feedback_data = {
            "message_id": "123",
            "user_id": 1,
            "feedback": "Great response!",
        }
        response = self.client.post("/feedback/submit", json=feedback_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "success")

        # Retrieve feedback
        response = self.client.get("/feedback/123")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json["feedback"]), 1)
        self.assertEqual(response.json["feedback"][0]["feedback"], "Great response!")

if __name__ == "__main__":
    unittest.main()
