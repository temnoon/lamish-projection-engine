#!/usr/bin/env python3
"""
Minimal test interface for the enhanced LPE system.
Demonstrates universal resubmit capabilities without complex dependencies.
"""

import sys
import os
import json
import http.server
import socketserver
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import time
import traceback
from datetime import datetime

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

# Import our new content system
from simple_content_models import (
    ContentItem, ProcessingParameters, ResubmitRequest, 
    create_text_content, create_image_content, get_available_engines
)
from simple_resubmit_system import get_registry, get_processor, create_resubmit_button_data


class MinimalLPEHandler(http.server.BaseHTTPRequestHandler):
    """Minimal HTTP handler to test universal resubmit capabilities."""
    
    def __init__(self, *args, **kwargs):
        self.registry = get_registry()
        self.processor = get_processor()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        path = urlparse(self.path).path
        query_params = parse_qs(urlparse(self.path).query)
        
        if path == '/':
            self.serve_main_interface()
        elif path == '/api/content/search':
            self.handle_content_search(query_params)
        elif path.startswith('/api/content/'):
            self.handle_content_api(path)
        elif path.startswith('/api/resubmit/'):
            self.handle_resubmit_options(path)
        else:
            self.send_404()
    
    def do_POST(self):
        path = urlparse(self.path).path
        
        if path.startswith('/api/resubmit/'):
            self.handle_resubmit_request(path)
        elif path == '/api/create_content':
            self.handle_create_content()
        else:
            self.send_404()
    
    def serve_main_interface(self):
        """Serve the minimal test interface."""
        
        # Get recent content for display
        recent_content = list(self.registry.content_items.values())[-10:]
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>LPE Enhanced System Test</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, sans-serif; 
            margin: 0; 
            background: #f8f9fa; 
            line-height: 1.6;
        }}
        .header {{ 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; 
            padding: 2rem; 
            text-align: center;
        }}
        .container {{ 
            max-width: 900px; 
            margin: 0 auto; 
            padding: 1rem; 
        }}
        .section {{ 
            background: white; 
            margin: 1rem 0; 
            padding: 1.5rem; 
            border-radius: 8px; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
        }}
        .content-item {{ 
            border: 1px solid #e0e0e0; 
            margin: 1rem 0; 
            padding: 1rem; 
            border-radius: 6px; 
            background: #fafafa; 
        }}
        .content-header {{ 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            margin-bottom: 0.5rem; 
        }}
        .content-title {{ 
            font-weight: bold; 
            color: #333; 
            font-size: 1.1rem;
        }}
        .content-type {{ 
            background: #667eea; 
            color: white; 
            padding: 0.25rem 0.75rem; 
            border-radius: 20px; 
            font-size: 0.8rem; 
            font-weight: 500;
        }}
        .content-preview {{ 
            color: #666; 
            font-size: 0.9rem; 
            margin: 0.75rem 0; 
            line-height: 1.4;
        }}
        .resubmit-buttons {{ 
            display: flex; 
            gap: 0.5rem; 
            flex-wrap: wrap; 
            margin-top: 1rem;
        }}
        .resubmit-btn {{ 
            background: #28a745; 
            color: white; 
            border: none; 
            padding: 0.4rem 0.8rem; 
            border-radius: 4px; 
            cursor: pointer; 
            font-size: 0.85rem; 
            font-weight: 500;
            transition: background-color 0.2s;
        }}
        .resubmit-btn:hover {{ 
            background: #218838; 
        }}
        .create-form {{ 
            display: grid; 
            gap: 1rem; 
        }}
        .form-group {{ 
            display: flex; 
            flex-direction: column; 
        }}
        .form-group label {{ 
            margin-bottom: 0.5rem; 
            font-weight: 600;
            color: #333;
        }}
        .form-group input, .form-group textarea, .form-group select {{ 
            padding: 0.75rem; 
            border: 1px solid #ddd; 
            border-radius: 4px; 
            font-size: 1rem;
        }}
        .form-group textarea {{
            resize: vertical;
            min-height: 100px;
        }}
        .submit-btn {{ 
            background: #667eea; 
            color: white; 
            border: none; 
            padding: 1rem 1.5rem; 
            border-radius: 4px; 
            cursor: pointer; 
            font-size: 1rem; 
            font-weight: 600;
            transition: background-color 0.2s;
        }}
        .submit-btn:hover {{ 
            background: #5a6fd8; 
        }}
        .search-box {{ 
            width: 100%; 
            padding: 0.75rem; 
            border: 1px solid #ddd; 
            border-radius: 4px; 
            margin-bottom: 1rem; 
            font-size: 1rem;
        }}
        .status-message {{
            padding: 1rem;
            border-radius: 4px;
            margin: 1rem 0;
        }}
        .success {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
        .error {{ background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
        .info {{ background: #cce7ff; color: #004085; border: 1px solid #99d6ff; }}
        .output-link {{
            display: inline-block;
            margin-top: 0.5rem;
            padding: 0.25rem 0.5rem;
            background: #007cba;
            color: white;
            text-decoration: none;
            border-radius: 3px;
            font-size: 0.8rem;
        }}
        .stats {{
            display: flex;
            gap: 2rem;
            text-align: center;
            margin: 1rem 0;
        }}
        .stat {{
            flex: 1;
        }}
        .stat-number {{
            font-size: 2rem;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            color: #666;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔮 LPE Enhanced System Test</h1>
        <p>Universal Content Processing with Allegorical Transformation</p>
        <p><em>Minimal test interface for the enhanced system</em></p>
    </div>
    
    <div class="container">
        <div class="section">
            <h2>📊 System Status</h2>
            <div class="stats">
                <div class="stat">
                    <div class="stat-number">{len(self.registry.content_items)}</div>
                    <div class="stat-label">Content Items</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{len(self.registry.processing_chains)}</div>
                    <div class="stat-label">Processing Chains</div>
                </div>
                <div class="stat">
                    <div class="stat-number">{len([f for f in self.registry.outputs_dir.glob("*") if f.is_dir()])}</div>
                    <div class="stat-label">Output Directories</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>➕ Create New Content</h2>
            <form class="create-form" onsubmit="createContent(event)">
                <div class="form-group">
                    <label for="content_type">Content Type</label>
                    <select id="content_type" name="content_type" required>
                        <option value="text">📝 Text</option>
                        <option value="image">🖼️ Image</option>
                        <option value="conversation">💬 Conversation</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label for="title">Title</label>
                    <input type="text" id="title" name="title" required 
                           placeholder="Enter a descriptive title...">
                </div>
                
                <div class="form-group">
                    <label for="content">Content</label>
                    <textarea id="content" name="content" rows="4" required 
                              placeholder="Enter your content here..."></textarea>
                </div>
                
                <button type="submit" class="submit-btn">Create Content</button>
            </form>
        </div>
        
        <div class="section">
            <h2>🔍 Search Content</h2>
            <input type="text" class="search-box" placeholder="Search content..." 
                   onkeyup="searchContent(this.value)">
            <div id="search-results"></div>
        </div>
        
        <div class="section">
            <h2>📚 Recent Content</h2>
            <div id="content-list">
                {self.render_content_list(recent_content)}
            </div>
        </div>
        
        <div id="status-area"></div>
    </div>
    
    <script>
        function showStatus(message, type = 'info') {{
            const statusArea = document.getElementById('status-area');
            statusArea.innerHTML = `<div class="status-message ${{type}}">${{message}}</div>`;
            setTimeout(() => statusArea.innerHTML = '', 5000);
        }}
        
        function createContent(event) {{
            event.preventDefault();
            
            const formData = new FormData(event.target);
            const data = Object.fromEntries(formData.entries());
            
            showStatus('Creating content...', 'info');
            
            fetch('/api/create_content', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify(data)
            }})
            .then(response => response.json())
            .then(result => {{
                if (result.success) {{
                    showStatus('Content created successfully!', 'success');
                    setTimeout(() => location.reload(), 1000);
                }} else {{
                    showStatus('Error: ' + result.error, 'error');
                }}
            }})
            .catch(error => {{
                showStatus('Error: ' + error, 'error');
            }});
        }}
        
        function searchContent(query) {{
            if (query.length < 2) {{
                document.getElementById('search-results').innerHTML = '';
                return;
            }}
            
            fetch(`/api/content/search?q=${{encodeURIComponent(query)}}`)
            .then(response => response.json())
            .then(results => {{
                const html = results.map(content => renderContentItem(content)).join('');
                document.getElementById('search-results').innerHTML = html || '<p>No results found.</p>';
            }})
            .catch(error => {{
                console.error('Search error:', error);
                showStatus('Search error: ' + error, 'error');
            }});
        }}
        
        function resubmitContent(contentId, engine) {{
            showStatus(`Resubmitting to ${{engine}}...`, 'info');
            
            const request = {{
                content_id: contentId,
                target_engine: engine,
                parameters: {{
                    persona: "neutral",
                    namespace: "lamish-galaxy",
                    style: "standard"
                }}
            }};
            
            fetch(`/api/resubmit/${{contentId}}`, {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify(request)
            }})
            .then(response => response.json())
            .then(result => {{
                if (result.success) {{
                    const message = `Content resubmitted to ${{engine}} successfully! 
                        <a href="file://${{result.output_directory}}" class="output-link">View Output</a>`;
                    showStatus(message, 'success');
                    setTimeout(() => location.reload(), 2000);
                }} else {{
                    showStatus('Error: ' + result.error, 'error');
                }}
            }})
            .catch(error => {{
                showStatus('Error: ' + error, 'error');
            }});
        }}
        
        function renderContentItem(content) {{
            const availableEngines = {self.get_available_engines_js()};
            const engines = availableEngines[content.content_type] || [];
            
            const engineButtons = engines.map(engine => 
                `<button class="resubmit-btn" onclick="resubmitContent('${{content.id}}', '${{engine}}')">${{engine}}</button>`
            ).join('');
            
            const preview = content.content.length > 150 ? 
                content.content.substring(0, 150) + '...' : content.content;
            
            return `
                <div class="content-item">
                    <div class="content-header">
                        <span class="content-title">${{content.title}}</span>
                        <span class="content-type">${{content.content_type}}</span>
                    </div>
                    <div class="content-preview">${{preview}}</div>
                    <div class="resubmit-buttons">
                        ${{engineButtons}}
                    </div>
                </div>
            `;
        }}
    </script>
</body>
</html>"""
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def render_content_list(self, content_list):
        """Render HTML for content list."""
        if not content_list:
            return "<p>No content yet. Create some content to get started!</p>"
        
        html_items = []
        for content in content_list:
            available_engines = get_available_engines(content)
            
            engine_buttons = ""
            for engine in available_engines:
                engine_buttons += f'''
                    <button class="resubmit-btn" onclick="resubmitContent('{content.id}', '{engine}')">
                        {engine}
                    </button>
                '''
            
            preview = content.content[:150] + "..." if len(content.content) > 150 else content.content
            
            html_items.append(f'''
                <div class="content-item">
                    <div class="content-header">
                        <span class="content-title">{content.title}</span>
                        <span class="content-type">{content.content_type}</span>
                    </div>
                    <div class="content-preview">{preview}</div>
                    <div class="resubmit-buttons">
                        {engine_buttons}
                    </div>
                </div>
            ''')
        
        return "".join(html_items)
    
    def get_available_engines_js(self):
        """Get available engines mapping for JavaScript."""
        return json.dumps({
            "text": ["projection", "translation", "maieutic", "refinement"],
            "image": ["vision", "echo_evolve"],
            "conversation": ["projection", "translation", "maieutic"],
            "projection": ["refinement"],
            "translation": ["refinement"]
        })
    
    def handle_create_content(self):
        """Handle content creation."""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)
            
            # Create content item
            content = create_text_content(
                data['content'],
                data['title'],
                content_type=data['content_type'],
                source="user_input"
            )
            
            # Register content
            content_id = self.registry.register_content(content)
            
            self.send_json_response({
                "success": True,
                "content_id": content_id,
                "message": "Content created successfully"
            })
            
        except Exception as e:
            self.send_json_response({
                "success": False,
                "error": str(e)
            })
    
    def handle_content_search(self, query_params):
        """Handle content search."""
        query = query_params.get('q', [''])[0]
        
        if len(query) < 2:
            self.send_json_response([])
            return
        
        try:
            results = self.registry.search_content(query)
            content_data = [content.to_dict() for content in results]
            self.send_json_response(content_data)
            
        except Exception as e:
            self.send_json_response({"error": str(e)})
    
    def handle_resubmit_request(self, path):
        """Handle resubmit request."""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            data = json.loads(post_data)
            
            # Create resubmit request
            request = ResubmitRequest(
                content_id=data['content_id'],
                target_engine=data['target_engine'],
                parameters=ProcessingParameters(**data.get('parameters', {}))
            )
            
            # Process resubmit
            output = self.processor.process_resubmit(request)
            
            self.send_json_response({
                "success": True,
                "output_directory": str(output.output_directory),
                "files_created": [str(f) for f in output.files_created],
                "content_id": output.content_item.id if output.content_item else None
            })
            
        except Exception as e:
            self.send_json_response({
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            })
    
    def handle_resubmit_options(self, path):
        """Handle getting resubmit options for content."""
        content_id = path.split('/')[-1]
        
        try:
            content = self.registry.get_content(content_id)
            if not content:
                self.send_json_response({"error": "Content not found"})
                return
            
            button_data = create_resubmit_button_data(content)
            self.send_json_response(button_data)
            
        except Exception as e:
            self.send_json_response({"error": str(e)})
    
    def handle_content_api(self, path):
        """Handle content API requests."""
        self.send_json_response({"message": "Content API endpoint"})
    
    def send_json_response(self, data):
        """Send JSON response."""
        response_data = json.dumps(data, indent=2, default=str)
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(response_data.encode('utf-8'))
    
    def send_404(self):
        """Send 404 response."""
        self.send_response(404)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'404 Not Found')
    
    def log_message(self, format, *args):
        """Custom logging."""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {format % args}")


def main():
    """Run the minimal test interface."""
    PORT = 8090  # Safe port for testing
    
    print("🔮 LPE Enhanced System Test Interface")
    print("=" * 50)
    print(f"Available at: http://localhost:{PORT}")
    print("Features:")
    print("  • Universal content resubmit system")
    print("  • File-based processing chains")
    print("  • Pydantic-free implementation")
    print("  • Ready for NAB integration")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 50)
    
    try:
        with socketserver.TCPServer(("", PORT), MinimalLPEHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\\n✅ Test interface stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")


if __name__ == "__main__":
    main()