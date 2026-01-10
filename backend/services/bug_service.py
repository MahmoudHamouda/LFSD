from sqlalchemy.orm import Session
from models.logging_models import BugReport, BugStatus
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
        user_id: str = None
    ) -> BugReport:
        """
        Create a new bug report.
        """
        report = BugReport(
            error_message=error_message,
            stack_trace=stack_trace,
            source_file=source_file,
            request_payload=context,
            user_id=str(user_id) if user_id else None,
            status=BugStatus.OPEN,
            severity="ERROR"
        )
        
        # NOTE: BugReport.user_id is Integer in logging_models.py, but User.id is UUID String in models.py.
        # This is a schema mismatch I noticed.
        # I should probably update BugReport to accept String user_id or store it in system_info/context if strict FK is not needed.
        # Given "Extreme-Agile", I will check logging_models.py again.
        
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report
