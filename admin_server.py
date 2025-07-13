#!/usr/bin/env python3
"""Clean admin interface for LPE job system - Port 8001."""
import sys
import os
import json
import http.server
import socketserver
from pathlib import Path
from urllib.parse import urlparse

# Add to path and import the jobs module directly
sys.path.insert(0, str(Path(__file__).parent))

# Import job system
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
print("LPE Admin Interface Starting...")
print("=" * 40)

job_manager = SimpleJobManager()
jobs = job_manager.list_jobs()

print(f"Database: {job_manager.db_path}")
print(f"Jobs found: {len(jobs)}")

# Web server handler
class AdminHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        
        if path == '/':
            jobs = job_manager.list_jobs()
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = f"""<!DOCTYPE html>
<html>
<head>
    <title>LPE Admin - Job System</title>
    <meta charset="utf-8">
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            margin: 40px; 
            background: #f5f5f5;
        }}
        .header {{ 
            background: white; 
            padding: 30px; 
            border-radius: 8px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .status {{ 
            color: #28a745; 
            font-weight: 600; 
        }}
        .nav {{ 
            margin: 20px 0; 
        }}
        .nav a {{ 
            margin-right: 15px; 
            padding: 12px 20px; 
            background: #007cba; 
            color: white; 
            text-decoration: none; 
            border-radius: 6px;
            font-weight: 500;
        }}
        .nav a:hover {{ background: #005a8b; }}
        .content {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        table {{ 
            border-collapse: collapse; 
            width: 100%; 
            font-size: 14px;
        }}
        th, td {{ 
            border: 1px solid #dee2e6; 
            padding: 12px 8px; 
            text-align: left; 
        }}
        th {{ 
            background-color: #f8f9fa; 
            font-weight: 600;
        }}
        .job-id {{ font-family: monospace; color: #6c757d; }}
        .status-pending {{ color: #ffc107; }}
        .status-running {{ color: #007cba; }}
        .status-completed {{ color: #28a745; }}
        .status-failed {{ color: #dc3545; }}
        .clickable-content {{ 
            cursor: pointer; 
            color: #007cba; 
            text-decoration: underline;
        }}
        .clickable-content:hover {{ 
            color: #005a8b; 
            background-color: #f8f9fa;
            padding: 2px 4px;
            border-radius: 3px;
        }}
        
        /* Modal Styles */
        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
        }}
        .modal-content {{
            background-color: white;
            margin: 5% auto;
            padding: 0;
            border-radius: 8px;
            width: 80%;
            max-width: 800px;
            max-height: 80vh;
            display: flex;
            flex-direction: column;
        }}
        .modal-header {{
            padding: 20px;
            border-bottom: 1px solid #dee2e6;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .modal-body {{
            padding: 20px;
            overflow-y: auto;
            flex: 1;
        }}
        .modal-actions {{
            padding: 15px 20px;
            border-top: 1px solid #dee2e6;
            display: flex;
            gap: 10px;
        }}
        .close-btn {{
            background: none;
            border: none;
            font-size: 24px;
            cursor: pointer;
            color: #6c757d;
        }}
        .close-btn:hover {{ color: #000; }}
        .action-btn {{
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }}
        .btn-copy {{ background: #007cba; color: white; }}
        .btn-copy:hover {{ background: #005a8b; }}
        .btn-save {{ background: #28a745; color: white; }}
        .btn-save:hover {{ background: #218838; }}
        .content-display {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            border: 1px solid #dee2e6;
            font-family: monospace;
            white-space: pre-wrap;
            word-wrap: break-word;
            max-height: 400px;
            overflow-y: auto;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>LPE Admin - Job System</h1>
        
        <div class="status">
            <p>Status: Operational</p>
            <p>Database: {job_manager.db_path}</p>
            <p>Jobs in Database: {len(jobs)}</p>
        </div>
        
        <div class="nav">
            <a href="/api/jobs">Jobs API</a>
            <a href="/api/status">Status API</a>
            <a href="/database">Database View</a>
            <a href="http://localhost:8000" target="_blank">User Interface</a>
        </div>
    </div>
    
    <div class="content">
        <h2>Recent Jobs</h2>
        <table>
            <tr>
                <th>Job ID</th>
                <th>Type</th>
                <th>Status</th>
                <th>Title</th>
                <th>Created</th>
                <th>Description</th>
            </tr>
"""
            
            for job in jobs[:15]:
                status_class = f"status-{job.status.value}"
                # Escape JSON data for HTML attributes
                input_data_str = json.dumps(job.input_data) if isinstance(job.input_data, dict) else str(job.input_data)
                result_data_str = json.dumps(job.result_data) if isinstance(job.result_data, dict) else str(job.result_data)
                input_data_escaped = input_data_str.replace('"', '&quot;').replace("'", '&#39;')
                result_data_escaped = result_data_str.replace('"', '&quot;').replace("'", '&#39;')
                
                html += f"""
            <tr>
                <td class="job-id">{job.id[:8]}...</td>
                <td>{job.type.value}</td>
                <td class="{status_class}">{job.status.value}</td>
                <td>{job.title}</td>
                <td>{job.created_at.strftime('%Y-%m-%d %H:%M')}</td>
                <td>
                    <span class="clickable-content" onclick="showModal('Input Data - {job.title}', '{input_data_escaped}', 'json')" title="Click to view input data">
                        📝 Input
                    </span>
                    {' | ' if job.result_data else ''}
                    {('<span class="clickable-content" onclick="showModal(\'Result Data - ' + job.title + '\', \'' + result_data_escaped + '\', \'json\')" title="Click to view result data">📊 Result</span>') if job.result_data else ''}
                </td>
            </tr>"""
            
            html += """
        </table>
    </div>
    
    <div class="content" style="margin-top: 20px;">
        <h3>System Information</h3>
        <p><strong>Working Directory:</strong> /Users/tem/lpe_dev</p>
        <p><strong>Job Types:</strong> Projection, Translation, Maieutic, Configuration</p>
        <p><strong>Features:</strong> Async processing, Real-time progress, WebSocket support</p>
        <p><strong>Mode:</strong> Admin interface (Port 8001)</p>
    </div>
    
    <!-- Content Modal -->
    <div id="contentModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3 id="modalTitle">Content Viewer</h3>
                <button class="close-btn" onclick="closeModal()">&times;</button>
            </div>
            <div class="modal-body">
                <div id="modalContent" class="content-display"></div>
            </div>
            <div class="modal-actions">
                <button class="action-btn btn-copy" onclick="copyModalContent()">📋 Copy</button>
                <button class="action-btn btn-save" onclick="saveModalContent()">💾 Save</button>
                <button class="action-btn" onclick="closeModal()">Close</button>
            </div>
        </div>
    </div>
    
    <script>
        let currentModalContent = '';
        
        function showModal(title, content, type) {
            // Unescape HTML entities
            content = content.replace(/&quot;/g, '"').replace(/&#39;/g, "'");
            
            document.getElementById('modalTitle').textContent = title;
            currentModalContent = content;
            
            let displayContent = content;
            if (type === 'json') {
                try {
                    const parsed = JSON.parse(content);
                    displayContent = JSON.stringify(parsed, null, 2);
                } catch (e) {
                    displayContent = content;
                }
            }
            
            document.getElementById('modalContent').textContent = displayContent;
            document.getElementById('contentModal').style.display = 'block';
        }
        
        function closeModal() {
            document.getElementById('contentModal').style.display = 'none';
        }
        
        function copyModalContent() {
            navigator.clipboard.writeText(currentModalContent).then(function() {
                // Show brief feedback
                const btn = document.querySelector('.btn-copy');
                const originalText = btn.textContent;
                btn.textContent = '✅ Copied!';
                setTimeout(() => {
                    btn.textContent = originalText;
                }, 2000);
            }).catch(function(err) {
                console.error('Copy failed:', err);
            });
        }
        
        function saveModalContent() {
            const title = document.getElementById('modalTitle').textContent;
            const blob = new Blob([currentModalContent], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${title.replace(/[^a-zA-Z0-9]/g, '_')}_${new Date().toISOString().slice(0,19).replace(/:/g,'-')}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
        
        // Close modal when clicking outside
        window.onclick = function(event) {
            const modal = document.getElementById('contentModal');
            if (event.target === modal) {
                closeModal();
            }
        }
    </script>
</body>
</html>"""
            
            self.wfile.write(html.encode('utf-8'))
        
        elif path == '/api/jobs':
            jobs = job_manager.list_jobs(limit=50)
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            job_data = [job.to_dict() for job in jobs]
            self.wfile.write(json.dumps(job_data, indent=2).encode('utf-8'))
        
        elif path == '/api/status':
            jobs = job_manager.list_jobs()
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            
            status = {
                "status": "operational",
                "interface": "admin",
                "port": 8001,
                "job_system": "active",
                "database_path": job_manager.db_path,
                "total_jobs": len(jobs),
                "recent_jobs": len([j for j in jobs if (datetime.now(timezone.utc) - j.created_at).days < 1]),
                "job_types": ["projection", "translation", "maieutic", "config_generation"],
                "working_directory": "/Users/tem/lpe_dev",
                "user_interface_url": "http://localhost:8000"
            }
            self.wfile.write(json.dumps(status, indent=2).encode('utf-8'))
        
        elif path == '/database':
            jobs = job_manager.list_jobs(limit=100)
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = f"""<!DOCTYPE html>
<html>
<head>
    <title>LPE Database Browser</title>
    <meta charset="utf-8">
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
            margin: 20px; 
            background: #f5f5f5;
        }}
        .content {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        table {{ 
            border-collapse: collapse; 
            width: 100%; 
            font-size: 12px; 
        }}
        th, td {{ 
            border: 1px solid #dee2e6; 
            padding: 8px; 
            text-align: left; 
        }}
        th {{ 
            background-color: #f8f9fa; 
            font-weight: 600;
        }}
        .back {{ margin: 20px 0; }}
        .back a {{ 
            padding: 10px 20px; 
            background: #6c757d; 
            color: white; 
            text-decoration: none; 
            border-radius: 6px;
        }}
        .job-id {{ font-family: monospace; }}
    </style>
</head>
<body>
    <div class="content">
        <h1>Database Contents</h1>
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
                <td class="job-id">{job.id[:8]}...</td>
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
            <a href="/">Back to Admin Dashboard</a>
        </div>
    </div>
</body>
</html>"""
            
            self.wfile.write(html.encode('utf-8'))
        
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'404 Not Found')
    
    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {format % args}")

print("\nStarting Admin Interface...")
print("Available at: http://localhost:8001")
print("Press Ctrl+C to stop")
print("=" * 40)

PORT = 8001
try:
    with socketserver.TCPServer(("", PORT), AdminHandler) as httpd:
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\nAdmin server stopped by user")
except Exception as e:
    print(f"Admin server error: {e}")