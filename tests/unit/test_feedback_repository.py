import unittest
from unittest.mock import MagicMock
from services.chat_service.db.feedback_repository import FeedbackRepository


class TestFeedbackRepository(unittest.TestCase):
    def setUp(self):
        self.db_session = MagicMock()
        self.repo = FeedbackRepository(self.db_session)

    def test_add_feedback(self):
        feedback_data = {
            "message_id": "123",
            "user_id": 1,
            "feedback": "Great response!",
        }
        self.repo.add_feedback(feedback_data)
        self.db_session.add.assert_called_once()
        self.db_session.commit.assert_called_once()

    def test_get_feedback_by_message_id(self):
        self.repo.get_feedback_by_message_id("123")
        self.db_session.query.assert_called_once()


if __name__ == "__main__":
    unittest.main()
