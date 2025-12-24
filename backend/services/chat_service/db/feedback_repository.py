from services.chat_service.models import Feedback
from shared.db_connection import db_session


class FeedbackRepository:
    @staticmethod
    def save_feedback(feedback_data):
        feedback = Feedback(**feedback_data)
        db_session.add(feedback)
        db_session.commit()

    @staticmethod
    def get_all_feedback():
        return db_session.query(Feedback).all()
