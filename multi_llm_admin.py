#!/usr/bin/env python3
"""Multi-Provider LLM Configuration Admin Interface - Port 8002."""

import sys
import os
import json
import http.server
import socketserver
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import urllib.request

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from llm_providers import llm_manager
from keychain_manager import keychain

class MultiLLMAdmin:
    def __init__(self):
        self.config_file = Path.home() / ".lpe" / "multi_llm_config.json"
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.load_config()
    
    def load_config(self):
        """Load multi-LLM configuration."""
        default_config = {
            "default_provider": "ollama",
            "provider_settings": {
                "openai": {
                    "default_model": "gpt-4",
                    "temperature": 0.7,
                    "max_tokens": 4096,
                    "timeout": 120
                },
                "anthropic": {
                    "default_model": "claude-3-sonnet-20240229", 
                    "temperature": 0.7,
                    "max_tokens": 4096,
                    "timeout": 120
                },
                "google": {
                    "default_model": "gemini-pro",
                    "temperature": 0.7,
                    "max_tokens": 4096,
                    "timeout": 120
                },
                "ollama": {
                    "default_model": "llama3.2:latest",
                    "temperature": 0.7,
                    "max_tokens": 4096,
                    "timeout": 120,
                    "host": "http://localhost:11434"
                }
            }
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults
                    self.config = default_config
                    self.config.update(loaded_config)
                    for provider, settings in loaded_config.get("provider_settings", {}).items():
                        if provider in self.config["provider_settings"]:
                            self.config["provider_settings"][provider].update(settings)
            except:
                self.config = default_config
        else:
            self.config = default_config
    
    def save_config(self):
        """Save multi-LLM configuration."""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)

class MultiLLMAdminHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.admin = MultiLLMAdmin()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        path = urlparse(self.path).path
        
        if path == '/':
            self.serve_admin_interface()
        elif path == '/api/config':
            self.serve_config_api()
        elif path == '/api/providers':
            self.serve_providers_api()
        elif path == '/api/keychain':
            self.serve_keychain_api()
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        path = urlparse(self.path).path
        
        if path == '/api/config':
            self.update_config()
        elif path == '/api/api-key':
            self.update_api_key()
        elif path == '/api/test':
            self.test_provider()
        else:
            self.send_response(404)
            self.end_headers()
    
    def serve_admin_interface(self):
        """Serve the multi-provider LLM admin interface."""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        providers_status = llm_manager.get_available_providers()
        keychain_status = keychain.list_stored_keys()
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Multi-Provider LLM Admin</title>
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
        .provider-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        .provider-header {{
            display: flex;
            justify-content: between;
            align-items: center;
            margin-bottom: 15px;
        }}
        .status-indicator {{
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }}
        .status-available {{ background: #d4edda; color: #155724; }}
        .status-unavailable {{ background: #f8d7da; color: #721c24; }}
        .status-keychain {{ background: #fff3cd; color: #856404; }}
        .form-group {{
            margin-bottom: 15px;
        }}
        label {{
            display: block;
            margin-bottom: 5px;
            font-weight: 600;
        }}
        select, input, textarea {{
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }}
        .btn {{
            background: #007cba;
            color: white;
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            margin-right: 8px;
        }}
        .btn:hover {{ background: #005a8b; }}
        .btn-danger {{ background: #dc3545; }}
        .btn-danger:hover {{ background: #c82333; }}
        .btn-success {{ background: #28a745; }}
        .btn-success:hover {{ background: #218838; }}
        .nav {{
            margin: 20px 0;
        }}
        .nav a {{
            margin-right: 15px;
            padding: 8px 16px;
            background: #6c757d;
            color: white;
            text-decoration: none;
            border-radius: 4px;
        }}
        .row {{ display: flex; gap: 20px; }}
        .col {{ flex: 1; }}
        .alert {{
            padding: 15px;
            border-radius: 4px;
            margin: 10px 0;
        }}
        .alert-success {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
        .alert-error {{ background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
        .keychain-info {{
            background: #e7f3ff;
            border: 1px solid #b8daff;
            padding: 15px;
            border-radius: 4px;
            margin: 15px 0;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔐 Multi-Provider LLM Admin</h1>
        <p>Configure OpenAI, Anthropic, Google, and Ollama providers with secure keychain storage</p>
        
        <div class="nav">
            <a href="http://localhost:8000" target="_blank">User Interface</a>
            <a href="http://localhost:8001" target="_blank">Job Admin</a>
            <a href="/api/config" target="_blank">Config API</a>
        </div>
    </div>
    
    <div id="alerts"></div>
    
    <div class="keychain-info">
        <h3>🔐 Secure API Key Storage</h3>
        <p>API keys are stored securely in macOS Keychain and never appear in config files.</p>
        <p><strong>Stored Keys:</strong> {', '.join([k for k, v in keychain_status.items() if v]) or 'None'}</p>
    </div>
"""

        # Generate provider cards
        for provider_name in ["openai", "anthropic", "google", "ollama"]:
            is_available = providers_status.get(provider_name, False)
            has_key = keychain_status.get(provider_name, False)
            models = llm_manager.get_provider_models(provider_name) if is_available else []
            settings = self.admin.config["provider_settings"].get(provider_name, {})
            
            # Status indicators
            if provider_name == "ollama":
                status_class = "status-available" if is_available else "status-unavailable"
                status_text = "Running" if is_available else "Not Running"
            else:
                if is_available:
                    status_class = "status-available"
                    status_text = "API Key Valid"
                elif has_key:
                    status_class = "status-keychain"
                    status_text = "API Key Stored"
                else:
                    status_class = "status-unavailable"
                    status_text = "No API Key"
            
            html += f"""
    <div class="provider-card">
        <div class="provider-header">
            <h2>{provider_name.title()}</h2>
            <span class="status-indicator {status_class}">{status_text}</span>
        </div>
        
        <div class="row">
            <div class="col">
"""
            
            # API Key section (not for Ollama)
            if provider_name != "ollama":
                html += f"""
                <div class="form-group">
                    <label for="{provider_name}_api_key">API Key:</label>
                    <input type="password" id="{provider_name}_api_key" 
                           placeholder="{'Key stored in keychain' if has_key else 'Enter API key'}">
                    <button class="btn" onclick="setApiKey('{provider_name}')">
                        {'Update' if has_key else 'Store'} Key
                    </button>
                    {f'<button class="btn btn-danger" onclick="deleteApiKey(\\"{provider_name}\\")">Delete Key</button>' if has_key else ''}
                </div>
"""
            
            # Model selection
            html += f"""
                <div class="form-group">
                    <label for="{provider_name}_model">Default Model:</label>
                    <select id="{provider_name}_model">
"""
            
            default_model = settings.get("default_model", "")
            if models:
                for model in models:
                    selected = "selected" if model == default_model else ""
                    html += f'<option value="{model}" {selected}>{model}</option>'
            else:
                html += f'<option value="{default_model}">{default_model}</option>'
            
            html += f"""
                    </select>
                </div>
            </div>
            <div class="col">
                <div class="form-group">
                    <label for="{provider_name}_temperature">Temperature:</label>
                    <input type="range" id="{provider_name}_temperature" min="0" max="2" step="0.1" 
                           value="{settings.get('temperature', 0.7)}"
                           oninput="document.getElementById('{provider_name}_temp_value').textContent = this.value">
                    <span id="{provider_name}_temp_value">{settings.get('temperature', 0.7)}</span>
                </div>
                
                <div class="form-group">
                    <label for="{provider_name}_max_tokens">Max Tokens:</label>
                    <select id="{provider_name}_max_tokens">
                        <option value="1024" {'selected' if settings.get('max_tokens') == 1024 else ''}>1024</option>
                        <option value="2048" {'selected' if settings.get('max_tokens') == 2048 else ''}>2048</option>
                        <option value="4096" {'selected' if settings.get('max_tokens') == 4096 else ''}>4096</option>
                        <option value="8192" {'selected' if settings.get('max_tokens') == 8192 else ''}>8192</option>
                    </select>
                </div>
            </div>
        </div>
        
        <button class="btn btn-success" onclick="testProvider('{provider_name}')">Test Connection</button>
        <button class="btn" onclick="saveProviderConfig('{provider_name}')">Save Settings</button>
    </div>
"""
        
        html += f"""
    <div class="provider-card">
        <h2>Global Settings</h2>
        <div class="form-group">
            <label for="default_provider">Default Provider:</label>
            <select id="default_provider">
"""
        
        current_default = self.admin.config.get("default_provider", "ollama")
        for provider_name in ["openai", "anthropic", "google", "ollama"]:
            selected = "selected" if provider_name == current_default else ""
            html += f'<option value="{provider_name}" {selected}>{provider_name.title()}</option>'
        
        html += f"""
            </select>
        </div>
        <button class="btn" onclick="saveGlobalConfig()">Save Global Settings</button>
    </div>
    
    <script>
        function showAlert(message, isError = false) {{
            const alerts = document.getElementById('alerts');
            const alert = document.createElement('div');
            alert.className = 'alert ' + (isError ? 'alert-error' : 'alert-success');
            alert.textContent = message;
            alerts.appendChild(alert);
            setTimeout(() => alert.remove(), 5000);
        }}
        
        function setApiKey(provider) {{
            const keyInput = document.getElementById(provider + '_api_key');
            const apiKey = keyInput.value.trim();
            
            if (!apiKey) {{
                showAlert('Please enter an API key', true);
                return;
            }}
            
            fetch('/api/api-key', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{provider: provider, api_key: apiKey}})
            }})
            .then(response => response.json())
            .then(data => {{
                if (data.success) {{
                    showAlert('API key stored securely in keychain');
                    keyInput.value = '';
                    keyInput.placeholder = 'Key stored in keychain';
                    setTimeout(() => location.reload(), 2000);
                }} else {{
                    showAlert('Error storing API key: ' + data.error, true);
                }}
            }})
            .catch(error => showAlert('Error: ' + error, true));
        }}
        
        function deleteApiKey(provider) {{
            if (!confirm('Delete API key for ' + provider + '?')) return;
            
            fetch('/api/api-key', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{provider: provider, delete: true}})
            }})
            .then(response => response.json())
            .then(data => {{
                if (data.success) {{
                    showAlert('API key deleted');
                    setTimeout(() => location.reload(), 2000);
                }} else {{
                    showAlert('Error deleting API key: ' + data.error, true);
                }}
            }})
            .catch(error => showAlert('Error: ' + error, true));
        }}
        
        function testProvider(provider) {{
            fetch('/api/test', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{provider: provider}})
            }})
            .then(response => response.json())
            .then(data => {{
                if (data.success) {{
                    showAlert(provider + ' connection successful!');
                }} else {{
                    showAlert(provider + ' test failed: ' + data.error, true);
                }}
            }})
            .catch(error => showAlert('Test error: ' + error, true));
        }}
        
        function saveProviderConfig(provider) {{
            const config = {{
                default_model: document.getElementById(provider + '_model').value,
                temperature: parseFloat(document.getElementById(provider + '_temperature').value),
                max_tokens: parseInt(document.getElementById(provider + '_max_tokens').value)
            }};
            
            fetch('/api/config', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{provider: provider, settings: config}})
            }})
            .then(response => response.json())
            .then(data => {{
                if (data.success) {{
                    showAlert(provider + ' settings saved');
                }} else {{
                    showAlert('Error saving settings: ' + data.error, true);
                }}
            }})
            .catch(error => showAlert('Error: ' + error, true));
        }}
        
        function saveGlobalConfig() {{
            const config = {{
                default_provider: document.getElementById('default_provider').value
            }};
            
            fetch('/api/config', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{global: config}})
            }})
            .then(response => response.json())
            .then(data => {{
                if (data.success) {{
                    showAlert('Global settings saved');
                }} else {{
                    showAlert('Error saving settings: ' + data.error, true);
                }}
            }})
            .catch(error => showAlert('Error: ' + error, true));
        }}
    </script>
</body>
</html>"""
        
        self.wfile.write(html.encode('utf-8'))
    
    def serve_config_api(self):
        """Serve current configuration as JSON."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        
        config_with_status = {
            **self.admin.config,
            "providers_status": llm_manager.get_available_providers(),
            "keychain_status": keychain.list_stored_keys()
        }
        
        self.wfile.write(json.dumps(config_with_status, indent=2).encode('utf-8'))
    
    def serve_providers_api(self):
        """Serve provider status."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        
        status = {
            "available": llm_manager.get_available_providers(),
            "models": {name: llm_manager.get_provider_models(name) for name in ["openai", "anthropic", "google", "ollama"]}
        }
        
        self.wfile.write(json.dumps(status).encode('utf-8'))
    
    def serve_keychain_api(self):
        """Serve keychain status."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        
        status = keychain.list_stored_keys()
        self.wfile.write(json.dumps(status).encode('utf-8'))
    
    def update_config(self):
        """Update configuration from POST data."""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            
            if 'provider' in data and 'settings' in data:
                # Update provider settings
                provider = data['provider']
                settings = data['settings']
                if provider in self.admin.config["provider_settings"]:
                    self.admin.config["provider_settings"][provider].update(settings)
            
            if 'global' in data:
                # Update global settings
                self.admin.config.update(data['global'])
            
            self.admin.save_config()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            
            response = {"success": True, "message": "Configuration updated"}
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            
            response = {"success": False, "error": str(e)}
            self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def update_api_key(self):
        """Store or delete API key."""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            provider = data.get('provider')
            
            if data.get('delete'):
                # Delete API key
                success = keychain.delete_api_key(provider)
                message = f"API key deleted for {provider}" if success else "Failed to delete API key"
            else:
                # Store API key
                api_key = data.get('api_key')
                success = llm_manager.set_api_key(provider, api_key)
                message = f"API key stored for {provider}" if success else "Failed to store API key"
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            
            response = {"success": success, "message": message}
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            
            response = {"success": False, "error": str(e)}
            self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def test_provider(self):
        """Test provider connection."""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            provider = data.get('provider')
            
            success = llm_manager.test_provider(provider)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            
            response = {"success": success, "provider": provider}
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            
            response = {"success": False, "error": str(e)}
            self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def log_message(self, format, *args):
        pass  # Suppress logging

print("Multi-Provider LLM Admin Starting...")
print("Available at: http://localhost:8002")

PORT = 8002
try:
    with socketserver.TCPServer(("", PORT), MultiLLMAdminHandler) as httpd:
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\\nMulti-LLM Admin stopped")
except Exception as e:
    print(f"Multi-LLM Admin error: {e}")