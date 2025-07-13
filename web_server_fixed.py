#!/usr/bin/env python3
"""Fixed web server for LPE job system."""
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

# Job system classes
class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class JobType(Enum):
    PROJECTION = "projection"
    TRANSLATION = "translation"
    MAIEUTIC = "maieutic"
    CONFIG_GENERATION = "config_generation"

@dataclass
class JobProgress:
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
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(Path.home() / ".lpe" / "jobs.db")
        
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
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
                    progress=None,
                    created_at=datetime.fromisoformat(row[9]),
                    started_at=datetime.fromisoformat(row[10]) if row[10] else None,
                    completed_at=datetime.fromisoformat(row[11]) if row[11] else None
                )
                jobs.append(job)
            
            return jobs

# Initialize job manager
print("🚀 LPE Job System Web Server")
print("=" * 40)

job_manager = SimpleJobManager()
jobs = job_manager.list_jobs()

print(f"✓ Database: {job_manager.db_path}")
print(f"✓ Jobs found: {len(jobs)}")

if jobs:
    print("\nRecent Jobs:")
    for job in jobs[:3]:
        print(f"  • {job.id[:8]}... | {job.type.value} | {job.status.value} | {job.title}")

# Web server handler
class LPEHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        
        if path == '/':
            jobs = job_manager.list_jobs()
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = f"""<!DOCTYPE html>
<html>
<head>
    <title>LPE Job System Status</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .status {{ color: green; font-weight: bold; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .nav {{ margin: 20px 0; }}
        .nav a {{ margin-right: 20px; padding: 10px; background: #007cba; color: white; text-decoration: none; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>🎭 Lamish Projection Engine - Job System</h1>
    
    <div class="status">
        <p>✓ Status: Operational</p>
        <p>✓ Database: {job_manager.db_path}</p>
        <p>✓ Jobs in Database: {len(jobs)}</p>
    </div>
    
    <div class="nav">
        <a href="/api/jobs">📋 API: Jobs (JSON)</a>
        <a href="/api/status">⚙️ API: Status (JSON)</a>
        <a href="/database">🗄️ Database View</a>
    </div>
    
    <h2>📊 Recent Jobs</h2>
    <table>
        <tr><th>ID</th><th>Type</th><th>Status</th><th>Title</th><th>Created</th></tr>
"""
            
            for job in jobs[:10]:
                html += f"""
        <tr>
            <td>{job.id[:8]}...</td>
            <td>{job.type.value}</td>
            <td>{job.status.value}</td>
            <td>{job.title}</td>
            <td>{job.created_at.strftime('%Y-%m-%d %H:%M')}</td>
        </tr>"""
            
            html += """
    </table>
    
    <div style="margin-top: 30px; padding: 20px; background: #f9f9f9; border-radius: 5px;">
        <h3>🔧 System Information</h3>
        <p><strong>Working Directory:</strong> /Users/tem/lpe_dev</p>
        <p><strong>Job Types:</strong> Projection, Translation, Maieutic, Configuration</p>
        <p><strong>Features:</strong> Async processing, Real-time progress, WebSocket support</p>
        <p><em>This is a simplified demo of the job system. Full web interface requires additional dependencies.</em></p>
    </div>
</body>
</html>"""
            
            self.wfile.write(html.encode())
        
        elif path == '/api/jobs':
            jobs = job_manager.list_jobs(limit=20)
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            job_data = [job.to_dict() for job in jobs]
            self.wfile.write(json.dumps(job_data, indent=2).encode())
        
        elif path == '/api/status':
            jobs = job_manager.list_jobs()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            status = {
                "status": "operational",
                "job_system": "active",
                "database_path": job_manager.db_path,
                "total_jobs": len(jobs),
                "recent_jobs": len([j for j in jobs if (datetime.now(timezone.utc) - j.created_at).days < 1]),
                "job_types": ["projection", "translation", "maieutic", "config_generation"],
                "working_directory": "/Users/tem/lpe_dev",
                "llm_mode": "mock (for demo)"
            }
            self.wfile.write(json.dumps(status, indent=2).encode())
        
        elif path == '/database':
            jobs = job_manager.list_jobs(limit=50)
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = f"""<!DOCTYPE html>
<html>
<head>
    <title>LPE Database Contents</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ border-collapse: collapse; width: 100%; font-size: 12px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .back {{ margin: 20px 0; }}
    </style>
</head>
<body>
    <h1>🗄️ Job Database Contents</h1>
    <p><strong>Database:</strong> {job_manager.db_path}</p>
    <p><strong>Total Jobs:</strong> {len(jobs)}</p>
    
    <table>
        <tr>
            <th>ID</th><th>Type</th><th>Status</th><th>Title</th>
            <th>Description</th><th>Created</th><th>Input Data</th>
        </tr>"""
            
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
        </tr>"""
            
            html += """
    </table>
    
    <div class="back">
        <a href="/">← Back to main page</a>
    </div>
</body>
</html>"""
            
            self.wfile.write(html.encode())
        
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'404 Not Found')
    
    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {format % args}")

print("\n🌐 Starting web server...")
print("📍 Available at: http://localhost:8002")
print("⏹️  Press Ctrl+C to stop")
print("=" * 40)

PORT = 8002
try:
    with socketserver.TCPServer(("", PORT), LPEHandler) as httpd:
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\n⏹️  Server stopped by user")
except Exception as e:
    print(f"❌ Server error: {e}")