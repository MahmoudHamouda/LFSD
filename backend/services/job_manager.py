import uuid
from typing import Dict, Any, Optional
from enum import Enum
from datetime import datetime

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class JobManager:
    _jobs: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def create_job(cls) -> str:
        job_id = str(uuid.uuid4())
        cls._jobs[job_id] = {
            "status": JobStatus.PENDING,
            "created_at": datetime.utcnow(),
            "result": None,
            "error": None,
            "progress": 0
        }
        return job_id

    @classmethod
    def update_job(cls, job_id: str, status: JobStatus, result: Optional[Dict] = None, error: Optional[str] = None, progress: int = 0):
        if job_id in cls._jobs:
            cls._jobs[job_id].update({
                "status": status,
                "result": result,
                "error": error,
                "progress": progress,
                "updated_at": datetime.utcnow()
            })

    @classmethod
    def get_job(cls, job_id: str) -> Optional[Dict[str, Any]]:
        return cls._jobs.get(job_id)

job_manager = JobManager()
