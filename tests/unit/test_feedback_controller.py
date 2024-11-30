import unittest
from unittest.mock import patch
from services.chat_service.controllers.feedback_controller import (
    submit_feedback,
    get_feedback,
)


class TestFeedbackController(unittest.TestCase):
    @patch(
        "services.chat_service.controllers.feedback_controller.FeedbackRepository"
    )
    def test_submit_feedback_success(self, MockFeedbackRepository):
        mock_repo = MockFeedbackRepository.return_value
        mock_repo.add_feedback.return_value = True

        data = {
            "message_id": "123",
            "user_id": 1,
            "feedback": "Great response!",
        }
        response = submit_feedback(data)

        self.assertEqual(response["status"], "success")
        self.assertEqual(
            response["message"], "Feedback submitted successfully."
        )
        mock_repo.add_feedback.assert_called_once_with(data)

    @patch(
        "services.chat_service.controllers.feedback_controller.FeedbackRepository"
    )
    def test_get_feedback_success(self, MockFeedbackRepository):
        mock_repo = MockFeedbackRepository.return_value
        mock_repo.get_feedback_by_message_id.return_value = [
            {
                "user_id": 1,
                "feedback": "Great response!",
                "created_at": "2024-11-30",
            }
        ]

        feedback = get_feedback("123")
        self.assertEqual(len(feedback), 1)
        self.assertEqual(feedback[0]["feedback"], "Great response!")
        mock_repo.get_feedback_by_message_id.assert_called_once_with("123")


if __name__ == "__main__":
    unittest.main()
