import uuid
from typing import Dict, Any, Optional
from enum import Enum
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from loguru import logger
from models.job import BackgroundJob
import json


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobManager:
    """
    Database-backed Job Manager.
    Ensures persistence, auditability, and thread-safety via DB transactions.
    """

    def __init__(self, db: Session):
        self.db = db

    def create_job(
        self, job_type: str, user_id: Optional[str] = None, source: str = "system"
    ) -> str:
        """Create a new tracked job."""
        try:
            job = BackgroundJob(
                id=str(uuid.uuid4()),
                job_type=job_type,
                user_id=user_id,
                source=source,
                status=JobStatus.PENDING,
                progress=0,
                expires_at=datetime.utcnow() + timedelta(days=7),  # 7-day retention
            )
            self.db.add(job)
            self.db.commit()
            self.db.refresh(job)
            logger.info(f"Job created: {job.id} ({job_type})")
            return job.id
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create job: {e}")
            raise e

    def update_job(
        self,
        job_id: str,
        status: JobStatus,
        result: Optional[Dict] = None,
        error: Optional[str] = None,
        progress: int = 0,
    ):
        """Update job state with validation."""
        try:
            job = (
                self.db.query(BackgroundJob).filter(BackgroundJob.id == job_id).first()
            )
            if not job:
                logger.warning(f"Attempted to update non-existent job: {job_id}")
                return

            # State Transition Validation (Basic)
            if (
                job.status in [JobStatus.COMPLETED, JobStatus.FAILED]
                and status == JobStatus.PROCESSING
            ):
                logger.warning(
                    f"Invalid transition from {job.status} to {status} for job {job_id}"
                )
                return

            job.status = status

            # Progress Guardrails
            if progress < 0:
                progress = 0
            if progress > 100:
                progress = 100
            job.progress = progress

            if result:
                job.result_json = result

            if error:
                job.error_message = error

            self.db.commit()

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update job {job_id}: {e}")

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve job details."""
        job = self.db.query(BackgroundJob).filter(BackgroundJob.id == job_id).first()
        if not job:
            return None

        return {
            "id": job.id,
            "status": job.status,
            "progress": job.progress,
            "result": job.result_json,
            "error": job.error_message,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
        }

    def cleanup_old_jobs(self):
        """Remove expired jobs."""
        try:
            now = datetime.utcnow()
            deleted = (
                self.db.query(BackgroundJob)
                .filter(BackgroundJob.expires_at < now)
                .delete()
            )
            self.db.commit()
            if deleted > 0:
                logger.info(f"Cleaned up {deleted} expired jobs.")
        except Exception as e:
            logger.error(f"Failed to cleanup jobs: {e}")
