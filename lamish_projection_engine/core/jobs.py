"""Job management system for long-running operations."""
import uuid
import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Callable, Union
from enum import Enum
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(Enum):
    """Job type enumeration."""
    PROJECTION = "projection"
    TRANSLATION = "translation"
    MAIEUTIC = "maieutic"
    CONFIG_GENERATION = "config_generation"


@dataclass
class JobProgress:
    """Progress information for a job."""
    current_step: str
    total_steps: int
    completed_steps: int
    percentage: float
    details: str
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "completed_steps": self.completed_steps,
            "percentage": self.percentage,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class Job:
    """Job representation."""
    id: str
    type: JobType
    status: JobStatus
    title: str
    description: str
    input_data: Dict[str, Any]
    result_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    progress: Optional[JobProgress]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "status": self.status.value,
            "title": self.title,
            "description": self.description,
            "input_data": self.input_data,
            "result_data": self.result_data,
            "error_message": self.error_message,
            "progress": self.progress.to_dict() if self.progress else None,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }


class JobManager:
    """Manages long-running jobs with database persistence."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize job manager."""
        self.db_path = db_path or str(Path.home() / ".lpe" / "jobs.db")
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.progress_callbacks: Dict[str, List[Callable]] = {}
        self.active_jobs: Dict[str, Job] = {}
        
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Load active jobs
        self._load_active_jobs()
    
    def _init_database(self):
        """Initialize the jobs database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    input_data TEXT,
                    result_data TEXT,
                    error_message TEXT,
                    progress TEXT,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT
                )
            """)
            conn.commit()
    
    def _load_active_jobs(self):
        """Load active jobs from database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM jobs 
                WHERE status IN ('pending', 'running')
                ORDER BY created_at DESC
            """)
            
            for row in cursor.fetchall():
                job = self._row_to_job(row)
                self.active_jobs[job.id] = job
    
    def _row_to_job(self, row) -> Job:
        """Convert database row to Job object."""
        (id_, type_, status, title, description, input_data, result_data, 
         error_message, progress, created_at, started_at, completed_at) = row
        
        return Job(
            id=id_,
            type=JobType(type_),
            status=JobStatus(status),
            title=title,
            description=description,
            input_data=json.loads(input_data) if input_data else {},
            result_data=json.loads(result_data) if result_data else None,
            error_message=error_message,
            progress=self._parse_progress(progress) if progress else None,
            created_at=datetime.fromisoformat(created_at),
            started_at=datetime.fromisoformat(started_at) if started_at else None,
            completed_at=datetime.fromisoformat(completed_at) if completed_at else None
        )
    
    def _parse_progress(self, progress_str: str) -> Optional[JobProgress]:
        """Parse progress JSON string to JobProgress object."""
        try:
            data = json.loads(progress_str)
            return JobProgress(
                current_step=data["current_step"],
                total_steps=data["total_steps"],
                completed_steps=data["completed_steps"],
                percentage=data["percentage"],
                details=data["details"],
                timestamp=datetime.fromisoformat(data["timestamp"])
            )
        except Exception as e:
            logger.error(f"Failed to parse progress: {e}")
            return None
    
    def _save_job(self, job: Job):
        """Save job to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO jobs 
                (id, type, status, title, description, input_data, result_data, 
                 error_message, progress, created_at, started_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job.id,
                job.type.value,
                job.status.value,
                job.title,
                job.description,
                json.dumps(job.input_data),
                json.dumps(job.result_data) if job.result_data else None,
                job.error_message,
                json.dumps(job.progress.to_dict()) if job.progress else None,
                job.created_at.isoformat(),
                job.started_at.isoformat() if job.started_at else None,
                job.completed_at.isoformat() if job.completed_at else None
            ))
            conn.commit()
    
    def create_job(self, job_type: JobType, title: str, description: str, 
                   input_data: Dict[str, Any]) -> str:
        """Create a new job and return its ID."""
        job_id = str(uuid.uuid4())
        
        job = Job(
            id=job_id,
            type=job_type,
            status=JobStatus.PENDING,
            title=title,
            description=description,
            input_data=input_data,
            result_data=None,
            error_message=None,
            progress=None,
            created_at=datetime.now(timezone.utc),
            started_at=None,
            completed_at=None
        )
        
        self.active_jobs[job_id] = job
        self._save_job(job)
        
        logger.info(f"Created job {job_id}: {title}")
        return job_id
    
    def update_progress(self, job_id: str, current_step: str, completed_steps: int, 
                       total_steps: int, details: str = ""):
        """Update job progress."""
        if job_id not in self.active_jobs:
            logger.warning(f"Job {job_id} not found for progress update")
            return
        
        job = self.active_jobs[job_id]
        percentage = (completed_steps / total_steps) * 100 if total_steps > 0 else 0
        
        job.progress = JobProgress(
            current_step=current_step,
            total_steps=total_steps,
            completed_steps=completed_steps,
            percentage=percentage,
            details=details,
            timestamp=datetime.now(timezone.utc)
        )
        
        self._save_job(job)
        
        # Notify progress callbacks
        if job_id in self.progress_callbacks:
            for callback in self.progress_callbacks[job_id]:
                try:
                    callback(job.progress)
                except Exception as e:
                    logger.error(f"Progress callback error: {e}")
        
        logger.info(f"Job {job_id} progress: {current_step} ({percentage:.1f}%)")
    
    def complete_job(self, job_id: str, result_data: Dict[str, Any]):
        """Mark job as completed with result data."""
        if job_id not in self.active_jobs:
            logger.warning(f"Job {job_id} not found for completion")
            return
        
        job = self.active_jobs[job_id]
        job.status = JobStatus.COMPLETED
        job.result_data = result_data
        job.completed_at = datetime.now(timezone.utc)
        
        self._save_job(job)
        
        # Clean up from active jobs
        del self.active_jobs[job_id]
        if job_id in self.progress_callbacks:
            del self.progress_callbacks[job_id]
        
        logger.info(f"Job {job_id} completed successfully")
    
    def fail_job(self, job_id: str, error_message: str):
        """Mark job as failed with error message."""
        if job_id not in self.active_jobs:
            logger.warning(f"Job {job_id} not found for failure")
            return
        
        job = self.active_jobs[job_id]
        job.status = JobStatus.FAILED
        job.error_message = error_message
        job.completed_at = datetime.now(timezone.utc)
        
        self._save_job(job)
        
        # Clean up from active jobs
        del self.active_jobs[job_id]
        if job_id in self.progress_callbacks:
            del self.progress_callbacks[job_id]
        
        logger.error(f"Job {job_id} failed: {error_message}")
    
    def start_job(self, job_id: str):
        """Mark job as started."""
        if job_id not in self.active_jobs:
            logger.warning(f"Job {job_id} not found for start")
            return
        
        job = self.active_jobs[job_id]
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc)
        
        self._save_job(job)
        logger.info(f"Job {job_id} started")
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        # Check active jobs first
        if job_id in self.active_jobs:
            return self.active_jobs[job_id]
        
        # Check database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_job(row)
        
        return None
    
    def list_jobs(self, limit: int = 50, status: Optional[JobStatus] = None) -> List[Job]:
        """List jobs with optional status filter."""
        with sqlite3.connect(self.db_path) as conn:
            if status:
                cursor = conn.execute("""
                    SELECT * FROM jobs WHERE status = ? 
                    ORDER BY created_at DESC LIMIT ?
                """, (status.value, limit))
            else:
                cursor = conn.execute("""
                    SELECT * FROM jobs 
                    ORDER BY created_at DESC LIMIT ?
                """, (limit,))
            
            return [self._row_to_job(row) for row in cursor.fetchall()]
    
    def add_progress_callback(self, job_id: str, callback: Callable[[JobProgress], None]):
        """Add a progress callback for a job."""
        if job_id not in self.progress_callbacks:
            self.progress_callbacks[job_id] = []
        self.progress_callbacks[job_id].append(callback)
    
    def cancel_job(self, job_id: str):
        """Cancel a job."""
        if job_id not in self.active_jobs:
            logger.warning(f"Job {job_id} not found for cancellation")
            return
        
        job = self.active_jobs[job_id]
        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.now(timezone.utc)
        
        self._save_job(job)
        
        # Clean up from active jobs
        del self.active_jobs[job_id]
        if job_id in self.progress_callbacks:
            del self.progress_callbacks[job_id]
        
        logger.info(f"Job {job_id} cancelled")
    
    def cleanup_old_jobs(self, days: int = 30):
        """Clean up jobs older than specified days."""
        cutoff = datetime.now(timezone.utc).replace(day=datetime.now().day - days)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM jobs 
                WHERE status IN ('completed', 'failed', 'cancelled') 
                AND created_at < ?
            """, (cutoff.isoformat(),))
            
            deleted = cursor.rowcount
            conn.commit()
            
        logger.info(f"Cleaned up {deleted} old jobs")
        return deleted


# Global job manager instance
_job_manager: Optional[JobManager] = None


def get_job_manager() -> JobManager:
    """Get the global job manager instance."""
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager()
    return _job_manager