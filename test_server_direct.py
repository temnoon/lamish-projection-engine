#!/usr/bin/env python3
"""Direct test of job system and simple web server."""
import sys
import os
import json
import http.server
import socketserver
from pathlib import Path
from urllib.parse import urlparse

# Add to path and import the jobs module directly
sys.path.insert(0, str(Path(__file__).parent))

# Import just the jobs functionality
import uuid
import sqlite3
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

# Job system classes (copied to avoid dependency issues)
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

class SimpleJobManager:
    """Simplified job manager for testing."""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(Path.home() / ".lpe" / "jobs.db")
        
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
    
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
    
    def create_job(self, job_type: JobType, title: str, description: str, 
                   input_data: Dict[str, Any]) -> str:
        """Create a new job and return its ID."""
        job_id = str(uuid.uuid4())
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO jobs 
                (id, type, status, title, description, input_data, result_data, 
                 error_message, progress, created_at, started_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id,
                job_type.value,
                JobStatus.PENDING.value,
                title,
                description,
                json.dumps(input_data),
                None,
                None,
                None,
                datetime.now(timezone.utc).isoformat(),
                None,
                None
            ))
            conn.commit()
        
        return job_id
    
    def list_jobs(self, limit: int = 50) -> List[Job]:
        """List jobs from database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT * FROM jobs 
                ORDER BY created_at DESC LIMIT ?
            """, (limit,))
            
            jobs = []
            for row in cursor.fetchall():
                job = Job(
                    id=row[0],
                    type=JobType(row[1]),
                    status=JobStatus(row[2]),
                    title=row[3],
                    description=row[4],
                    input_data=json.loads(row[5]) if row[5] else {},
                    result_data=json.loads(row[6]) if row[6] else None,
                    error_message=row[7],
                    progress=None,  # Simplified for now
                    created_at=datetime.fromisoformat(row[9]),
                    started_at=datetime.fromisoformat(row[10]) if row[10] else None,
                    completed_at=datetime.fromisoformat(row[11]) if row[11] else None
                )
                jobs.append(job)
            
            return jobs

# Initialize job manager
print("Initializing LPE Job System...")
job_manager = SimpleJobManager()

# Create some test jobs
print("Creating test jobs...")
job1 = job_manager.create_job(
    JobType.PROJECTION,
    "Test Projection",
    "Creating allegorical projection of startup story",
    {"narrative": "Sam Altman dropped out of Stanford", "persona": "philosopher"}
)

job2 = job_manager.create_job(
    JobType.TRANSLATION,
    "Test Translation",
    "Round-trip translation analysis",
    {"text": "Innovation drives progress", "language": "spanish"}
)

job3 = job_manager.create_job(
    JobType.MAIEUTIC,
    "Test Dialogue",
    "Socratic questioning session",
    {"narrative": "Technology shapes society", "goal": "understand"}
)

print(f"✓ Created test jobs: {job1[:8]}..., {job2[:8]}..., {job3[:8]}...")

# List all jobs
jobs = job_manager.list_jobs()
print(f"✓ Database contains {len(jobs)} jobs")

print("\nJob Database Contents:")
print("=" * 80)
for job in jobs:
    print(f"ID: {job.id[:8]}... | Type: {job.type.value:12} | Status: {job.status.value:9} | Title: {job.title}")
    print(f"    Description: {job.description}")
    print(f"    Created: {job.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"    Input: {str(job.input_data)[:60]}...")
    print()

print("=" * 80)

# Start simple web server
class LPEHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        
        if path == '/':\n            jobs = job_manager.list_jobs()
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = f"""
            <!DOCTYPE html>
            <html>
            <head><title>LPE Job System Status</title></head>
            <body>
                <h1>Lamish Projection Engine - Job System</h1>
                <p><strong>Status:</strong> ✓ Operational</p>
                <p><strong>Database:</strong> {job_manager.db_path}</p>
                <p><strong>Jobs in Database:</strong> {len(jobs)}</p>
                
                <h2>API Endpoints:</h2>
                <ul>
                    <li><a href="/api/jobs">/api/jobs</a> - List all jobs (JSON)</li>
                    <li><a href="/api/status">/api/status</a> - System status (JSON)</li>
                    <li><a href="/database">/database</a> - Database contents (HTML)</li>
                </ul>
                
                <h2>Recent Jobs:</h2>
                <table border="1" style="border-collapse: collapse; width: 100%;">
                    <tr><th>ID</th><th>Type</th><th>Status</th><th>Title</th><th>Created</th></tr>
            """
            
            for job in jobs[:5]:  # Show latest 5 jobs
                html += f"""
                    <tr>
                        <td>{job.id[:8]}...</td>
                        <td>{job.type.value}</td>
                        <td>{job.status.value}</td>
                        <td>{job.title}</td>
                        <td>{job.created_at.strftime('%Y-%m-%d %H:%M')}</td>
                    </tr>
                """
            
            html += """
                </table>
                <p><em>This is a simplified demo of the job system functionality.</em></p>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
        
        elif path == '/api/jobs':
            jobs = job_manager.list_jobs(limit=20)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            job_data = [job.to_dict() for job in jobs]
            self.wfile.write(json.dumps(job_data, indent=2).encode())
        
        elif path == '/api/status':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            status = {
                "status": "operational",
                "job_system": "active",
                "database_path": job_manager.db_path,
                "total_jobs": len(jobs),
                "recent_jobs": len([j for j in jobs if (datetime.now(timezone.utc) - j.created_at).days < 1]),
                "llm_mode": "mock (for demo)"
            }
            self.wfile.write(json.dumps(status, indent=2).encode())
        
        elif path == '/database':
            jobs = job_manager.list_jobs(limit=50)
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = f"""
            <!DOCTYPE html>
            <html>
            <head><title>LPE Database Contents</title></head>
            <body>
                <h1>Job Database Contents</h1>
                <p><strong>Database:</strong> {job_manager.db_path}</p>
                <p><strong>Total Jobs:</strong> {len(jobs)}</p>
                
                <table border="1" style="border-collapse: collapse; width: 100%; font-size: 12px;">
                    <tr>
                        <th>ID</th><th>Type</th><th>Status</th><th>Title</th>
                        <th>Description</th><th>Created</th><th>Input Data</th>
                    </tr>
            """
            
            for job in jobs:
                input_preview = str(job.input_data)[:50] + "..." if len(str(job.input_data)) > 50 else str(job.input_data)
                html += f"""
                    <tr>
                        <td>{job.id[:8]}...</td>
                        <td>{job.type.value}</td>
                        <td>{job.status.value}</td>
                        <td>{job.title}</td>
                        <td>{job.description}</td>
                        <td>{job.created_at.strftime('%Y-%m-%d %H:%M')}</td>
                        <td>{input_preview}</td>
                    </tr>
                """
            
            html += """
                </table>
                <p><a href="/">← Back to main page</a></p>
            </body>
            </html>
            """
            
            self.wfile.write(html.encode())
        
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'404 Not Found')
    
    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {format % args}")

print("\nStarting web server...")
print("Available at: http://localhost:8001")
print("Press Ctrl+C to stop")
print("=" * 50)

PORT = 8001
try:
    with socketserver.TCPServer(("", PORT), LPEHandler) as httpd:
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\nServer stopped by user")
except Exception as e:
    print(f"Server error: {e}")