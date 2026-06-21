from sqlalchemy.orm import Session
from models.logging_models import BugReport, BugStatus, BugSeverity
import traceback


class BugService:
    def __init__(self, db: Session):
        self.db = db

    def create_report(
        self,
        error_message: str,
        stack_trace: str,
        source_file: str = None,
        context: dict = None,
        user_id: str = None,
    ) -> BugReport:
        """
        Create a new bug report.
        """
        report = BugReport(
            error_message=error_message,
            stack_trace=stack_trace,
            source_file=source_file,
            system_info=context or {},  # Using system_info field from model
            user_id=str(user_id) if user_id else None,
            status=BugStatus.OPEN,
            severity=BugSeverity.ERROR,
        )

        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report
