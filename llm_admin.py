#!/usr/bin/env python3
"""LLM Configuration Admin Interface - Port 8002."""
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

# Import configurations
from model_config import task_model_config
from llm_providers import llm_manager

class LLMAdmin:
    def __init__(self):
        self.config_file = Path.home() / ".lpe" / "llm_config.json"
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.load_config()
    
    def load_config(self):
        """Load LLM configuration."""
        default_config = {
            "llm_model": "llama3.2:latest",
            "embedding_model": "nomic-embed-text:latest", 
            "temperature": 0.7,
            "max_tokens": 8192,
            "timeout": 120,
            "ollama_host": "http://localhost:11434"
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = {**default_config, **json.load(f)}
            except:
                self.config = default_config
        else:
            self.config = default_config
    
    def save_config(self):
        """Save LLM configuration."""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get_available_models(self):
        """Get available models from Ollama."""
        try:
            url = f"{self.config['ollama_host']}/api/tags"
            response = urllib.request.urlopen(url, timeout=5)
            data = json.loads(response.read().decode())
            return [m.get('name', '') for m in data.get('models', [])]
        except Exception as e:
            print(f"Error getting models: {e}")
            return []
    
    def get_available_providers(self):
        """Get available providers and their models."""
        providers = {
            "openai": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "dall-e-3"],
            "anthropic": ["claude-3-sonnet-20240229", "claude-3-haiku-20240307", "claude-3-opus-20240229"],
            "google": ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.5-pro", "gemini-2.5-flash"],
            "ollama": self.get_available_models()
        }
        return providers

class LLMAdminHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.admin = LLMAdmin()
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        path = urlparse(self.path).path
        
        if path == '/':
            self.serve_admin_interface()
        elif path == '/api/config':
            self.serve_config_api()
        elif path == '/api/models':
            self.serve_models_api()
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        path = urlparse(self.path).path
        
        if path == '/api/config':
            self.update_config()
        elif path == '/api/task-config':
            self.update_task_config()
        else:
            self.send_response(404)
            self.end_headers()
    
    def generate_task_config_html(self):
        """Generate HTML for task-specific model configuration."""
        providers = self.admin.get_available_providers()
        tasks = task_model_config.get_available_tasks()
        
        html_parts = []
        
        for task in tasks:
            task_config = task_model_config.get_task_config(task)
            display_name = task_model_config.get_task_display_name(task)
            
            # Special handling for image generation
            if task == "image_generation":
                html_parts.append(f"""
                <div class="form-group" style="border: 1px solid #ddd; padding: 20px; border-radius: 6px; margin-bottom: 20px;">
                    <h3>{display_name}</h3>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div>
                            <label for="{task}_cloud_provider">Cloud Provider:</label>
                            <select id="{task}_cloud_provider" name="{task}_cloud_provider">
                                {''.join(f'<option value="{provider}" {"selected" if provider == task_config.get("cloud_provider") else ""}>{provider.title()}</option>' for provider in ["openai"])}
                            </select>
                            <label for="{task}_cloud_model">Cloud Model:</label>
                            <select id="{task}_cloud_model" name="{task}_cloud_model">
                                {''.join(f'<option value="{model}" {"selected" if model == task_config.get("cloud_model") else ""}>{model}</option>' for model in providers.get("openai", []))}
                            </select>
                        </div>
                        
                        <div>
                            <label for="{task}_local_provider">Local Provider:</label>
                            <select id="{task}_local_provider" name="{task}_local_provider">
                                <option value="ollamadiffuser" {"selected" if task_config.get("local_provider") == "ollamadiffuser" else ""}>OllamaDiffuser</option>
                            </select>
                            <label for="{task}_local_model">Local Model:</label>
                            <select id="{task}_local_model" name="{task}_local_model">
                                <option value="flux.1-schnell" {"selected" if task_config.get("local_model") == "flux.1-schnell" else ""}>FLUX.1 Schnell</option>
                                <option value="flux.1-dev" {"selected" if task_config.get("local_model") == "flux.1-dev" else ""}>FLUX.1 Dev</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label for="{task}_default_provider">Default Provider:</label>
                        <select id="{task}_default_provider" name="{task}_default_provider">
                            <option value="openai" {"selected" if task_config.get("default_provider") == "openai" else ""}>OpenAI (Cloud)</option>
                            <option value="ollamadiffuser" {"selected" if task_config.get("default_provider") == "ollamadiffuser" else ""}>OllamaDiffuser (Local)</option>
                        </select>
                    </div>
                </div>
                """)
            else:
                # Regular LLM tasks
                html_parts.append(f"""
                <div class="form-group" style="border: 1px solid #ddd; padding: 20px; border-radius: 6px; margin-bottom: 20px;">
                    <h3>{display_name}</h3>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px;">
                        <div>
                            <label for="{task}_provider">Provider:</label>
                            <select id="{task}_provider" name="{task}_provider">
                                {''.join(f'<option value="{provider}" {"selected" if provider == task_config.get("provider") else ""}>{provider.title()}</option>' for provider in providers.keys())}
                            </select>
                        </div>
                        
                        <div>
                            <label for="{task}_model">Model:</label>
                            <select id="{task}_model" name="{task}_model">
                                {''.join(f'<option value="{model}" {"selected" if model == task_config.get("model") else ""}>{model}</option>' for model in providers.get(task_config.get("provider", "google"), []))}
                            </select>
                        </div>
                        
                        <div>
                            <label for="{task}_temperature">Temperature:</label>
                            <input type="range" id="{task}_temperature" name="{task}_temperature" 
                                   min="0" max="2" step="0.1" value="{task_config.get('temperature', 0.7)}"
                                   oninput="document.getElementById('{task}_temp_val').textContent = this.value">
                            <span id="{task}_temp_val">{task_config.get('temperature', 0.7)}</span>
                        </div>
                    </div>
                </div>
                """)
        
        return ''.join(html_parts)

    def serve_admin_interface(self):
        """Serve the LLM admin interface."""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        available_models = self.admin.get_available_models()
        providers = self.admin.get_available_providers()
        providers_json = json.dumps(providers)
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>LLM Configuration Admin</title>
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
        .content {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .form-group {{
            margin-bottom: 20px;
        }}
        label {{
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
        }}
        select, input {{
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
        }}
        .btn {{
            background: #007cba;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            margin-right: 10px;
        }}
        .btn:hover {{ background: #005a8b; }}
        .btn-secondary {{
            background: #6c757d;
        }}
        .status {{
            padding: 15px;
            border-radius: 6px;
            margin: 20px 0;
        }}
        .status.success {{
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }}
        .status.error {{
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }}
        .model-info {{
            background: #e9ecef;
            padding: 15px;
            border-radius: 6px;
            margin: 10px 0;
        }}
        .nav {{
            margin: 20px 0;
        }}
        .nav a {{
            margin-right: 15px;
            padding: 12px 20px;
            background: #6c757d;
            color: white;
            text-decoration: none;
            border-radius: 6px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>LLM Configuration Admin</h1>
        <p>Configure language models and embedding models for the LPE system</p>
        
        <div class="nav">
            <a href="http://localhost:8000" target="_blank">User Interface</a>
            <a href="http://localhost:8001" target="_blank">Job Admin</a>
            <a href="/api/config" target="_blank">Config API</a>
        </div>
    </div>
    
    <div class="content">
        <div id="status" style="display: none;"></div>
        
        <form id="config-form">
            <h2>Task-Specific Model Configuration</h2>
            <p>Configure different models for specific LLM tasks to optimize performance.</p>
            
            <div id="task-configs">
                {self.generate_task_config_html()}
            </div>
            
            <h2>Legacy Model Configuration</h2>
            
            <div class="form-group">
                <label for="llm_model">Primary LLM Model:</label>
                <select id="llm_model" name="llm_model">
                    {''.join(f'<option value="{model}" {"selected" if model == self.admin.config["llm_model"] else ""}>{model}</option>' for model in available_models)}
                </select>
                <small>Main model for text generation (projections, translations, maieutic dialogue)</small>
            </div>
            
            <div class="form-group">
                <label for="embedding_model">Embedding Model:</label>
                <select id="embedding_model" name="embedding_model">
                    {''.join(f'<option value="{model}" {"selected" if model == self.admin.config["embedding_model"] else ""}>{model}</option>' for model in available_models)}
                </select>
                <small>Model for text embeddings and semantic analysis</small>
            </div>
            
            <h2>Generation Parameters</h2>
            
            <div class="form-group">
                <label for="temperature">Temperature:</label>
                <input type="range" id="temperature" name="temperature" 
                       min="0" max="2" step="0.1" value="{self.admin.config['temperature']}"
                       oninput="document.getElementById('temp-value').textContent = this.value">
                <span id="temp-value">{self.admin.config['temperature']}</span>
                <small>Controls randomness (0 = deterministic, 2 = very random)</small>
            </div>
            
            <div class="form-group">
                <label for="max_tokens">Max Tokens:</label>
                <select id="max_tokens" name="max_tokens">
                    <option value="2048" {"selected" if self.admin.config['max_tokens'] == 2048 else ""}>2048 (Short responses)</option>
                    <option value="4096" {"selected" if self.admin.config['max_tokens'] == 4096 else ""}>4096 (Medium responses)</option>
                    <option value="8192" {"selected" if self.admin.config['max_tokens'] == 8192 else ""}>8192 (Long responses)</option>
                    <option value="16384" {"selected" if self.admin.config['max_tokens'] == 16384 else ""}>16384 (Very long responses)</option>
                </select>
                <small>Maximum length of generated responses</small>
            </div>
            
            <div class="form-group">
                <label for="timeout">Request Timeout (seconds):</label>
                <select id="timeout" name="timeout">
                    <option value="60" {"selected" if self.admin.config['timeout'] == 60 else ""}>60 seconds</option>
                    <option value="120" {"selected" if self.admin.config['timeout'] == 120 else ""}>120 seconds</option>
                    <option value="300" {"selected" if self.admin.config['timeout'] == 300 else ""}>300 seconds</option>
                </select>
                <small>How long to wait for LLM responses</small>
            </div>
            
            <h2>Connection Settings</h2>
            
            <div class="form-group">
                <label for="ollama_host">Ollama Host:</label>
                <input type="text" id="ollama_host" name="ollama_host" 
                       value="{self.admin.config['ollama_host']}"
                       placeholder="http://localhost:11434">
                <small>URL of the Ollama API server</small>
            </div>
            
            <button type="submit" class="btn">Save Legacy Configuration</button>
            <button type="button" class="btn btn-secondary" onclick="testConnection()">Test Connection</button>
            <button type="button" class="btn" onclick="saveTaskConfig()">Save Task Configuration</button>
        </form>
        
        <div class="model-info">
            <h3>Available Models</h3>
            <ul>
                {''.join(f'<li>{model}</li>' for model in available_models)}
            </ul>
        </div>
    </div>
    
    <script>
        function showStatus(message, isError = false) {{
            const status = document.getElementById('status');
            status.className = 'status ' + (isError ? 'error' : 'success');
            status.textContent = message;
            status.style.display = 'block';
            setTimeout(() => status.style.display = 'none', 5000);
        }}
        
        document.getElementById('config-form').addEventListener('submit', function(e) {{
            e.preventDefault();
            
            const formData = new FormData(this);
            const config = {{}};
            for (let [key, value] of formData.entries()) {{
                if (key === 'temperature') {{
                    config[key] = parseFloat(value);
                }} else if (key === 'max_tokens' || key === 'timeout') {{
                    config[key] = parseInt(value);
                }} else {{
                    config[key] = value;
                }}
            }}
            
            fetch('/api/config', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify(config)
            }})
            .then(response => response.json())
            .then(data => {{
                if (data.success) {{
                    showStatus('Configuration saved successfully!');
                }} else {{
                    showStatus('Error saving configuration: ' + data.error, true);
                }}
            }})
            .catch(error => {{
                showStatus('Error: ' + error, true);
            }});
        }});
        
        function testConnection() {{
            fetch('/api/models')
            .then(response => response.json())
            .then(data => {{
                if (data.success) {{
                    showStatus(`Connection successful! Found ${{data.models.length}} models.`);
                }} else {{
                    showStatus('Connection failed: ' + data.error, true);
                }}
            }})
            .catch(error => {{
                showStatus('Connection test failed: ' + error, true);
            }});
        }}
        
        // Provider-model mapping
        const providerModels = {providers_json};
        
        function updateModelDropdown(task, provider) {{
            const modelSelect = document.getElementById(task + '_model');
            const models = providerModels[provider] || [];
            
            // Clear existing options
            modelSelect.innerHTML = '';
            
            // Add new options
            models.forEach(model => {{
                const option = document.createElement('option');
                option.value = model;
                option.textContent = model;
                modelSelect.appendChild(option);
            }});
        }}
        
        // Add event listeners for provider changes
        document.addEventListener('DOMContentLoaded', function() {{
            const tasks = ['projection', 'translation', 'maieutic', 'vision_transcription', 'vision_analysis'];
            
            tasks.forEach(task => {{
                const providerSelect = document.getElementById(task + '_provider');
                if (providerSelect) {{
                    providerSelect.addEventListener('change', function() {{
                        updateModelDropdown(task, this.value);
                    }});
                }}
            }});
            
            // Special handling for image generation cloud provider
            const imageCloudProviderSelect = document.getElementById('image_generation_cloud_provider');
            if (imageCloudProviderSelect) {{
                imageCloudProviderSelect.addEventListener('change', function() {{
                    const modelSelect = document.getElementById('image_generation_cloud_model');
                    const models = providerModels[this.value] || [];
                    
                    modelSelect.innerHTML = '';
                    models.forEach(model => {{
                        const option = document.createElement('option');
                        option.value = model;
                        option.textContent = model;
                        modelSelect.appendChild(option);
                    }});
                }});
            }}
        }});
        
        function saveTaskConfig() {{
            const taskConfig = {{}};
            const tasks = ['projection', 'translation', 'maieutic', 'vision_transcription', 'vision_analysis', 'image_generation'];
            
            tasks.forEach(task => {{
                if (task === 'image_generation') {{
                    taskConfig[task] = {{
                        cloud_provider: document.getElementById(task + '_cloud_provider').value,
                        cloud_model: document.getElementById(task + '_cloud_model').value,
                        local_provider: document.getElementById(task + '_local_provider').value,
                        local_model: document.getElementById(task + '_local_model').value,
                        default_provider: document.getElementById(task + '_default_provider').value
                    }};
                }} else {{
                    taskConfig[task] = {{
                        provider: document.getElementById(task + '_provider').value,
                        model: document.getElementById(task + '_model').value,
                        temperature: parseFloat(document.getElementById(task + '_temperature').value)
                    }};
                }}
            }});
            
            fetch('/api/task-config', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify(taskConfig)
            }})
            .then(response => response.json())
            .then(data => {{
                if (data.success) {{
                    showStatus('Task configuration saved successfully!');
                }} else {{
                    showStatus('Error saving task configuration: ' + data.error, true);
                }}
            }})
            .catch(error => {{
                showStatus('Error: ' + error, true);
            }});
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
        
        self.wfile.write(json.dumps(self.admin.config, indent=2).encode('utf-8'))
    
    def serve_models_api(self):
        """Serve available models."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        
        try:
            models = self.admin.get_available_models()
            response = {"success": True, "models": models}
        except Exception as e:
            response = {"success": False, "error": str(e)}
        
        self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def update_config(self):
        """Update configuration from POST data."""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            new_config = json.loads(post_data.decode('utf-8'))
            self.admin.config.update(new_config)
            self.admin.save_config()
            
            # Update environment variables
            os.environ['LPE_LLM_MODEL'] = self.admin.config['llm_model']
            os.environ['LPE_LLM_MAX_TOKENS'] = str(self.admin.config['max_tokens'])
            os.environ['LPE_LLM_TEMPERATURE'] = str(self.admin.config['temperature'])
            
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
    
    def update_task_config(self):
        """Update task-specific model configuration."""
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            new_config = json.loads(post_data.decode('utf-8'))
            
            # Update each task configuration
            for task, config in new_config.items():
                task_model_config.update_task_config(task, config)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            
            response = {"success": True, "message": "Task configuration updated"}
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            
            response = {"success": False, "error": str(e)}
            self.wfile.write(json.dumps(response).encode('utf-8'))
    
    def log_message(self, format, *args):
        pass  # Suppress logging

print("LLM Configuration Admin Starting...")
print("Available at: http://localhost:8002")

PORT = 8002
try:
    with socketserver.TCPServer(("", PORT), LLMAdminHandler) as httpd:
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\nLLM Admin stopped")
except Exception as e:
    print(f"LLM Admin error: {e}")