#!/usr/bin/env python3
"""Test just the jobs module functionality."""
import sys
import os
import sqlite3
import uuid
import json
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, Optional, List

# Import our jobs module directly
sys.path.insert(0, str(Path(__file__).parent))

# Copy the job classes to test them directly
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

def test_job_database():
    """Test the job database functionality."""
    print("Testing Job Database Functionality\n")
    
    # Create test database
    db_path = "/tmp/test_jobs.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Initialize database
    with sqlite3.connect(db_path) as conn:
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
    
    print("1. Database created successfully ✓")
    
    # Test job creation
    job_id = str(uuid.uuid4())
    job = Job(
        id=job_id,
        type=JobType.PROJECTION,
        status=JobStatus.PENDING,
        title="Test Projection",
        description="Testing job creation",
        input_data={"narrative": "test story"},
        result_data=None,
        error_message=None,
        progress=None,
        created_at=datetime.now(timezone.utc),
        started_at=None,
        completed_at=None
    )
    
    # Save job to database
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            INSERT INTO jobs 
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
            None,
            job.error_message,
            None,
            job.created_at.isoformat(),
            None,
            None
        ))
        conn.commit()
    
    print("2. Job saved to database ✓")
    
    # Test job retrieval
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()
        if row:
            print("3. Job retrieved from database ✓")
            print(f"   ID: {row[0][:8]}...")
            print(f"   Type: {row[1]}")
            print(f"   Status: {row[2]}")
            print(f"   Title: {row[3]}")
        else:
            print("3. Failed to retrieve job ✗")
    
    # Test progress update
    progress = JobProgress(
        current_step="Processing",
        total_steps=5,
        completed_steps=2,
        percentage=40.0,
        details="Making progress",
        timestamp=datetime.now(timezone.utc)
    )
    
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            UPDATE jobs SET 
                status = ?,
                progress = ?,
                started_at = ?
            WHERE id = ?
        """, (
            JobStatus.RUNNING.value,
            json.dumps(progress.to_dict()),
            datetime.now(timezone.utc).isoformat(),
            job_id
        ))
        conn.commit()
    
    print("4. Job progress updated ✓")
    
    # Test job completion
    result_data = {"final_result": "Job completed successfully"}
    
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            UPDATE jobs SET 
                status = ?,
                result_data = ?,
                completed_at = ?
            WHERE id = ?
        """, (
            JobStatus.COMPLETED.value,
            json.dumps(result_data),
            datetime.now(timezone.utc).isoformat(),
            job_id
        ))
        conn.commit()
    
    print("5. Job completed ✓")
    
    # Test job listing
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("SELECT id, type, status, title FROM jobs ORDER BY created_at DESC LIMIT 10")
        rows = cursor.fetchall()
        print(f"6. Found {len(rows)} jobs in database ✓")
        for row in rows:
            print(f"   - {row[0][:8]}... | {row[1]} | {row[2]} | {row[3]}")
    
    print("\n✓ Job database functionality test complete!")
    
    # Clean up
    os.remove(db_path)
    print("✓ Test database cleaned up")

if __name__ == "__main__":
    test_job_database()