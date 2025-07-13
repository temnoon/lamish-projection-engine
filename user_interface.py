#!/usr/bin/env python3
"""Main user interface for LPE - Port 8000."""
import sys
import os
import json
import http.server
import socketserver
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# Add to path and mock missing dependencies
sys.path.insert(0, str(Path(__file__).parent))

# Mock the config import to avoid pydantic dependency
sys.modules['lamish_projection_engine.utils.config'] = __import__('simple_config')

# Force mock LLM
os.environ['LPE_USE_MOCK_LLM'] = 'true'

# Import job system
import uuid
import sqlite3
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

# Job system classes (same as admin)
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

class SimpleJobManager:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(Path.home() / ".lpe" / "jobs.db")
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY, type TEXT NOT NULL, status TEXT NOT NULL,
                    title TEXT NOT NULL, description TEXT, input_data TEXT,
                    result_data TEXT, error_message TEXT, progress TEXT,
                    created_at TEXT NOT NULL, started_at TEXT, completed_at TEXT
                )
            """)
            conn.commit()
    
    def create_job(self, job_type: JobType, title: str, description: str, input_data: Dict[str, Any]) -> str:
        job_id = str(uuid.uuid4())
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO jobs 
                (id, type, status, title, description, input_data, result_data, 
                 error_message, progress, created_at, started_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id, job_type.value, JobStatus.PENDING.value, title, description,
                json.dumps(input_data), None, None, None,
                datetime.now(timezone.utc).isoformat(), None, None
            ))
            conn.commit()
        return job_id

# Initialize
job_manager = SimpleJobManager()

print("LPE User Interface Starting...")
print("Available at: http://localhost:8000")
print("Admin interface: http://localhost:8001")

class UserInterfaceHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        
        if path == '/':
            self.serve_main_interface()
        elif path == '/api/projection/create':
            self.handle_api_request()
        elif path == '/api/translation/round-trip':
            self.handle_api_request()
        elif path == '/api/maieutic/start':
            self.handle_api_request()
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
        except:
            data = {}
        
        path = urlparse(self.path).path
        
        if path == '/api/projection/create':
            self.handle_projection_request(data)
        elif path == '/api/translation/round-trip':
            self.handle_translation_request(data)
        elif path == '/api/maieutic/start':
            self.handle_maieutic_request(data)
        else:
            self.send_response(404)
            self.end_headers()
    
    def handle_projection_request(self, data):
        job_id = job_manager.create_job(
            JobType.PROJECTION,
            f"Allegorical Projection",
            f"Transforming: {data.get('narrative', '')[:50]}...",
            data
        )
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "job_id": job_id,
            "message": "Projection job started",
            "status": "pending"
        }
        self.wfile.write(json.dumps(response).encode())
    
    def handle_translation_request(self, data):
        job_id = job_manager.create_job(
            JobType.TRANSLATION,
            f"Translation Analysis",
            f"Round-trip via {data.get('intermediate_language', 'unknown')}",
            data
        )
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "job_id": job_id,
            "message": "Translation job started",
            "status": "pending"
        }
        self.wfile.write(json.dumps(response).encode())
    
    def handle_maieutic_request(self, data):
        job_id = job_manager.create_job(
            JobType.MAIEUTIC,
            f"Maieutic Dialogue",
            f"Exploring: {data.get('narrative', '')[:50]}...",
            data
        )
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
        response = {
            "job_id": job_id,
            "message": "Maieutic dialogue started",
            "status": "pending"
        }
        self.wfile.write(json.dumps(response).encode())
    
    def serve_main_interface(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Lamish Projection Engine</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <style>
        .nav-link.active { background-color: #0d6efd !important; color: white !important; }
        .progress-container { margin: 20px 0; }
        .job-status { padding: 15px; border-radius: 5px; margin: 10px 0; }
        .status-pending { background-color: #fff3cd; border: 1px solid #ffeaa7; }
        .status-completed { background-color: #d1edff; border: 1px solid #74b9ff; }
        .admin-link { position: fixed; top: 10px; right: 10px; z-index: 1000; }
    </style>
</head>
<body>
    <a href="http://localhost:8001" target="_blank" class="btn btn-sm btn-secondary admin-link">Admin</a>
    
    <div class="container-fluid">
        <div class="row">
            <!-- Header -->
            <div class="col-12 bg-primary text-white p-3">
                <h1>Lamish Projection Engine</h1>
                <p class="mb-0">AI-powered allegorical narrative transformation system</p>
            </div>
        </div>
        
        <div class="row">
            <!-- Sidebar -->
            <div class="col-md-3 bg-light p-3">
                <nav class="nav flex-column">
                    <a class="nav-link active" href="#projection">Projection</a>
                    <a class="nav-link" href="#maieutic">Maieutic Dialogue</a>
                    <a class="nav-link" href="#translation">Round-trip Translation</a>
                    <a class="nav-link" href="#configuration">Configuration</a>
                </nav>
            </div>
            
            <!-- Main Content -->
            <div class="col-md-9 p-3">
                <!-- Projection Tab -->
                <div id="projection" class="tab-content active">
                    <h2>Create Projection</h2>
                    <form id="projection-form">
                        <div class="mb-3">
                            <label for="narrative" class="form-label">Narrative Text</label>
                            <textarea class="form-control" id="narrative" rows="4" 
                                     placeholder="Enter the narrative to transform..."></textarea>
                        </div>
                        <div class="row">
                            <div class="col-md-4">
                                <label for="persona" class="form-label">Persona</label>
                                <select class="form-control" id="persona">
                                    <option value="">Use current configuration</option>
                                    <option value="neutral">Neutral</option>
                                    <option value="advocate">Advocate</option>
                                    <option value="critic">Critic</option>
                                    <option value="philosopher">Philosopher</option>
                                    <option value="storyteller">Storyteller</option>
                                </select>
                            </div>
                            <div class="col-md-4">
                                <label for="namespace" class="form-label">Namespace</label>
                                <select class="form-control" id="namespace">
                                    <option value="">Use current configuration</option>
                                    <option value="lamish-galaxy">Lamish Galaxy</option>
                                    <option value="medieval-realm">Medieval Realm</option>
                                    <option value="corporate-dystopia">Corporate Dystopia</option>
                                    <option value="natural-world">Natural World</option>
                                </select>
                            </div>
                            <div class="col-md-4">
                                <label for="style" class="form-label">Style</label>
                                <select class="form-control" id="style">
                                    <option value="">Use current configuration</option>
                                    <option value="standard">Standard</option>
                                    <option value="academic">Academic</option>
                                    <option value="poetic">Poetic</option>
                                    <option value="technical">Technical</option>
                                </select>
                            </div>
                        </div>
                        <div class="mt-3">
                            <button type="submit" class="btn btn-primary">Create Projection</button>
                        </div>
                    </form>
                    
                    <div id="projection-result" class="mt-4" style="display: none;"></div>
                </div>
                
                <!-- Maieutic Tab -->
                <div id="maieutic" class="tab-content" style="display: none;">
                    <h2>Maieutic (Socratic) Dialogue</h2>
                    <form id="maieutic-form">
                        <div class="mb-3">
                            <label for="maieutic-narrative" class="form-label">Narrative to Explore</label>
                            <textarea class="form-control" id="maieutic-narrative" rows="4" 
                                     placeholder="Enter the narrative you want to explore through Socratic questioning..."></textarea>
                        </div>
                        <div class="row">
                            <div class="col-md-6">
                                <label for="dialogue-goal" class="form-label">Exploration Goal</label>
                                <select class="form-control" id="dialogue-goal">
                                    <option value="understand">Understand</option>
                                    <option value="clarify">Clarify</option>
                                    <option value="discover">Discover</option>
                                    <option value="question">Question</option>
                                </select>
                            </div>
                            <div class="col-md-6">
                                <label for="max-turns" class="form-label">Maximum Turns</label>
                                <select class="form-control" id="max-turns">
                                    <option value="3">3</option>
                                    <option value="5" selected>5</option>
                                    <option value="7">7</option>
                                    <option value="10">10</option>
                                </select>
                            </div>
                        </div>
                        <div class="mt-3">
                            <button type="submit" class="btn btn-primary">Start Dialogue</button>
                        </div>
                    </form>
                    
                    <div id="maieutic-result" class="mt-4" style="display: none;"></div>
                </div>
                
                <!-- Translation Tab -->
                <div id="translation" class="tab-content" style="display: none;">
                    <h2>Round-trip Translation Analysis</h2>
                    <form id="translation-form">
                        <div class="mb-3">
                            <label for="translation-text" class="form-label">Text to Analyze</label>
                            <textarea class="form-control" id="translation-text" rows="4" 
                                     placeholder="Enter text for round-trip analysis..."></textarea>
                        </div>
                        <div class="row">
                            <div class="col-md-6">
                                <label for="intermediate-language" class="form-label">Intermediate Language</label>
                                <select class="form-control" id="intermediate-language">
                                    <option value="spanish">Spanish</option>
                                    <option value="french">French</option>
                                    <option value="german">German</option>
                                    <option value="chinese">Chinese</option>
                                    <option value="arabic">Arabic</option>
                                </select>
                            </div>
                        </div>
                        <div class="mt-3">
                            <button type="submit" class="btn btn-primary">Analyze Translation</button>
                        </div>
                    </form>
                    
                    <div id="translation-result" class="mt-4" style="display: none;"></div>
                </div>
                
                <!-- Configuration Tab -->
                <div id="configuration" class="tab-content" style="display: none;">
                    <h2>Dynamic Configuration</h2>
                    <div class="alert alert-info">
                        <h5>Configuration System</h5>
                        <p>Dynamic attribute configuration is available through the full LPE system. 
                        This demo interface creates jobs that would normally configure:</p>
                        <ul>
                            <li><strong>Persona Attributes:</strong> Character traits and perspectives</li>
                            <li><strong>Namespace Attributes:</strong> Fictional universe settings</li>
                            <li><strong>Language Style:</strong> Writing tone and approach</li>
                        </ul>
                        <p>Jobs created here are stored in the database and visible in the 
                        <a href="http://localhost:8001" target="_blank">Admin Interface</a>.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Tab navigation
        $('.nav-link').click(function(e) {
            e.preventDefault();
            $('.nav-link').removeClass('active');
            $('.tab-content').hide();
            $(this).addClass('active');
            $($(this).attr('href')).show();
        });
        
        // Show job status
        function showJobStatus(containerId, jobId, title, message) {
            const statusHtml = `
                <div class="job-status status-pending">
                    <h5>${title}</h5>
                    <p><strong>Job ID:</strong> ${jobId}</p>
                    <p><strong>Status:</strong> ${message}</p>
                    <p>This job has been queued for processing. In the full system, you would see real-time progress updates.</p>
                    <p><a href="http://localhost:8001" target="_blank">View in Admin Interface</a></p>
                </div>
            `;
            $(containerId).html(statusHtml).show();
        }
        
        // Projection form
        $('#projection-form').submit(function(e) {
            e.preventDefault();
            
            const data = {
                narrative: $('#narrative').val(),
                persona: $('#persona').val() || null,
                namespace: $('#namespace').val() || null,
                style: $('#style').val() || null,
                show_steps: true
            };
            
            $.ajax({
                url: '/api/projection/create',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify(data),
                success: function(result) {
                    showJobStatus('#projection-result', result.job_id, 
                                'Projection Job Created', result.message);
                },
                error: function(xhr) {
                    alert('Error starting projection: ' + (xhr.responseJSON?.detail || 'Unknown error'));
                }
            });
        });
        
        // Maieutic form
        $('#maieutic-form').submit(function(e) {
            e.preventDefault();
            
            const data = {
                narrative: $('#maieutic-narrative').val(),
                goal: $('#dialogue-goal').val(),
                max_turns: parseInt($('#max-turns').val())
            };
            
            $.ajax({
                url: '/api/maieutic/start',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify(data),
                success: function(result) {
                    showJobStatus('#maieutic-result', result.job_id, 
                                'Maieutic Dialogue Job Created', result.message);
                },
                error: function(xhr) {
                    alert('Error starting dialogue: ' + (xhr.responseJSON?.detail || 'Unknown error'));
                }
            });
        });
        
        // Translation form
        $('#translation-form').submit(function(e) {
            e.preventDefault();
            
            const data = {
                text: $('#translation-text').val(),
                intermediate_language: $('#intermediate-language').val(),
                source_language: 'english'
            };
            
            $.ajax({
                url: '/api/translation/round-trip',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify(data),
                success: function(result) {
                    showJobStatus('#translation-result', result.job_id, 
                                'Translation Analysis Job Created', result.message);
                },
                error: function(xhr) {
                    alert('Error starting translation: ' + (xhr.responseJSON?.detail || 'Unknown error'));
                }
            });
        });
    </script>
</body>
</html>"""
        
        self.wfile.write(html.encode('utf-8'))
    
    def log_message(self, format, *args):
        # Suppress logging for cleaner output
        pass

PORT = 8000
try:
    with socketserver.TCPServer(("", PORT), UserInterfaceHandler) as httpd:
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\nUser interface stopped")
except Exception as e:
    print(f"User interface error: {e}")