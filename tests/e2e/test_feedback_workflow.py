import unittest
from services.chat_service.app import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class TestFeedbackWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine(
            "sqlite:///:memory:"
        )  # In-memory DB for testing
        cls.Session = sessionmaker(bind=cls.engine)
        cls.app = app
        cls.app.testing = True
        cls.client = cls.app.test_client()

    def test_feedback_workflow(self):
        # Step 1: Submit feedback
        feedback_data = {
            "message_id": "124",
            "user_id": 2,
            "feedback": "Needs improvement.",
        }
        response = self.client.post("/feedback/submit", json=feedback_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "success")

        # Step 2: Retrieve feedback
        response = self.client.get("/feedback/124")
        self.assertEqual(response.status_code, 200)
        feedback = response.json["feedback"]
        self.assertEqual(len(feedback), 1)
        self.assertEqual(feedback[0]["feedback"], "Needs improvement.")


if __name__ == "__main__":
    unittest.main()
