#!/usr/bin/env python3
"""Simple web server launcher without external dependencies."""
import sys
import os
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

# Mock the config and other modules that require external dependencies
sys.modules['lamish_projection_engine.utils.config'] = __import__('simple_config')

# Force mock LLM to avoid dependency issues
os.environ['LPE_USE_MOCK_LLM'] = 'true'

print("Starting LPE Web Server with job system...")
print("Note: Using mock LLM due to dependency constraints")

try:
    # Try to import and test the job system first
    from lamish_projection_engine.core.jobs import get_job_manager
    
    print("✓ Job system loading...")
    job_manager = get_job_manager()
    print(f"✓ Job manager initialized")
    
    # Test database creation
    test_job_id = job_manager.create_job(
        job_manager.JobType.PROJECTION,
        "System Test Job",
        "Testing system startup",
        {"test": "data"}
    )
    print(f"✓ Test job created: {test_job_id[:8]}...")
    
    # List jobs to verify database works
    jobs = job_manager.list_jobs(limit=5)
    print(f"✓ Database operational, found {len(jobs)} jobs")
    
    print("\n" + "="*50)
    print("JOB SYSTEM STATUS:")
    print("="*50)
    
    for job in jobs:
        print(f"Job: {job.id[:8]}... | {job.type.value} | {job.status.value}")
        print(f"     Title: {job.title}")
        print(f"     Created: {job.created_at}")
        if job.progress:
            print(f"     Progress: {job.progress.current_step} ({job.progress.percentage:.1f}%)")
        print()
    
    print("="*50)
    print("Starting web server on http://localhost:8000")
    print("Press Ctrl+C to stop")
    print("="*50)
    
    # Start a simple HTTP server to demonstrate the API
    import http.server
    import socketserver
    import json
    from urllib.parse import urlparse, parse_qs
    
    class LPEHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            path = urlparse(self.path).path
            
            if path == '/':
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                html = """
                <!DOCTYPE html>
                <html>
                <head><title>LPE Job System</title></head>
                <body>
                    <h1>Lamish Projection Engine - Job System</h1>
                    <p>✓ Job system is operational</p>
                    <h2>API Endpoints:</h2>
                    <ul>
                        <li><a href="/api/jobs">/api/jobs</a> - List jobs</li>
                        <li><a href="/api/status">/api/status</a> - System status</li>
                        <li><a href="/database">/database</a> - Database contents</li>
                    </ul>
                    <p><em>Note: Full web interface requires additional dependencies</em></p>
                </body>
                </html>
                """
                self.wfile.write(html.encode())
            
            elif path == '/api/jobs':
                jobs = job_manager.list_jobs(limit=10)
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
                    "database": str(job_manager.db_path),
                    "active_jobs": len(job_manager.active_jobs),
                    "llm_mode": "mock"
                }
                self.wfile.write(json.dumps(status, indent=2).encode())
            
            elif path == '/database':
                jobs = job_manager.list_jobs(limit=20)
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                
                html = """
                <!DOCTYPE html>
                <html>
                <head><title>LPE Database Contents</title></head>
                <body>
                    <h1>Job Database Contents</h1>
                    <table border="1" style="border-collapse: collapse; width: 100%;">
                        <tr>
                            <th>ID</th><th>Type</th><th>Status</th><th>Title</th>
                            <th>Created</th><th>Progress</th>
                        </tr>
                """
                
                for job in jobs:
                    progress = ""
                    if job.progress:
                        progress = f"{job.progress.current_step} ({job.progress.percentage:.1f}%)"
                    
                    html += f"""
                        <tr>
                            <td>{job.id[:8]}...</td>
                            <td>{job.type.value}</td>
                            <td>{job.status.value}</td>
                            <td>{job.title}</td>
                            <td>{job.created_at.strftime('%Y-%m-%d %H:%M')}</td>
                            <td>{progress}</td>
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
                self.wfile.write(b'Not found')
        
        def log_message(self, format, *args):
            # Suppress default logging
            pass
    
    PORT = 8000
    with socketserver.TCPServer(("", PORT), LPEHandler) as httpd:
        print(f"Server running at http://localhost:{PORT}")
        httpd.serve_forever()

except Exception as e:
    print(f"Error starting server: {e}")
    import traceback
    traceback.print_exc()