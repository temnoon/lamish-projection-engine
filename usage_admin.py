#!/usr/bin/env python3
"""Token usage dashboard - Port 8003."""

import sys
import os
import json
import http.server
import socketserver
from pathlib import Path
from urllib.parse import urlparse

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from token_meter import token_meter

class UsageAdminHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        
        if path == '/':
            self.serve_usage_dashboard()
        elif path == '/api/usage/summary':
            self.serve_usage_summary()
        elif path == '/api/usage/daily':
            self.serve_daily_usage()
        else:
            self.send_response(404)
            self.end_headers()
    
    def serve_usage_dashboard(self):
        """Serve the token usage dashboard."""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Token Usage Dashboard</title>
    <meta charset="utf-8">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        .usage-card { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            color: white; 
        }
        .cost-card { 
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
            color: white; 
        }
        .token-card { 
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
            color: white; 
        }
        .provider-card {
            border-left: 4px solid #007cba;
            margin-bottom: 15px;
        }
    </style>
</head>
<body>
    <div class="container-fluid mt-4">
        <div class="row">
            <div class="col-12">
                <h1>💰 Token Usage Dashboard</h1>
                <p class="text-muted">Monitor LLM token consumption and costs across all providers</p>
                
                <div class="nav mb-4">
                    <a href="http://localhost:8000" class="btn btn-outline-primary me-2">User Interface</a>
                    <a href="http://localhost:8001" class="btn btn-outline-secondary me-2">Job Admin</a>
                    <a href="http://localhost:8002" class="btn btn-outline-info me-2">LLM Admin</a>
                </div>
            </div>
        </div>
        
        <!-- Summary Cards -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card usage-card">
                    <div class="card-body text-center">
                        <h2 id="total-requests">-</h2>
                        <p class="mb-0">Total Requests</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card cost-card">
                    <div class="card-body text-center">
                        <h2 id="total-cost">-</h2>
                        <p class="mb-0">Total Cost (7 days)</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card token-card">
                    <div class="card-body text-center">
                        <h2 id="total-input-tokens">-</h2>
                        <p class="mb-0">Input Tokens</p>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card token-card">
                    <div class="card-body text-center">
                        <h2 id="total-output-tokens">-</h2>
                        <p class="mb-0">Output Tokens</p>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Usage by Provider -->
        <div class="row">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">
                        <h5>Usage by Provider (Last 7 Days)</h5>
                    </div>
                    <div class="card-body">
                        <canvas id="providerChart"></canvas>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h5>Provider Breakdown</h5>
                    </div>
                    <div class="card-body" id="provider-breakdown">
                        <!-- Provider details will be loaded here -->
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Daily Usage -->
        <div class="row mt-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5>Today's Usage</h5>
                    </div>
                    <div class="card-body">
                        <div id="daily-usage">
                            <!-- Daily usage details will be loaded here -->
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let providerChart = null;
        
        function loadUsageSummary() {
            fetch('/api/usage/summary')
                .then(response => response.json())
                .then(data => {
                    // Update summary cards
                    document.getElementById('total-requests').textContent = data.total_requests.toLocaleString();
                    document.getElementById('total-cost').textContent = '$' + data.total_cost.toFixed(4);
                    document.getElementById('total-input-tokens').textContent = (data.total_input_tokens / 1000).toFixed(1) + 'K';
                    document.getElementById('total-output-tokens').textContent = (data.total_output_tokens / 1000).toFixed(1) + 'K';
                    
                    // Update provider chart
                    updateProviderChart(data.by_provider);
                    
                    // Update provider breakdown
                    updateProviderBreakdown(data.by_provider);
                })
                .catch(error => console.error('Error loading usage summary:', error));
        }
        
        function loadDailyUsage() {
            fetch('/api/usage/daily')
                .then(response => response.json())
                .then(data => {
                    updateDailyUsage(data);
                })
                .catch(error => console.error('Error loading daily usage:', error));
        }
        
        function updateProviderChart(providers) {
            const ctx = document.getElementById('providerChart').getContext('2d');
            
            const labels = Object.keys(providers);
            const costs = labels.map(provider => providers[provider].cost);
            const requests = labels.map(provider => providers[provider].requests);
            
            if (providerChart) {
                providerChart.destroy();
            }
            
            providerChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Cost ($)',
                        data: costs,
                        backgroundColor: 'rgba(54, 162, 235, 0.8)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1,
                        yAxisID: 'y'
                    }, {
                        label: 'Requests',
                        data: requests,
                        backgroundColor: 'rgba(255, 99, 132, 0.8)',
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 1,
                        yAxisID: 'y1'
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            grid: {
                                drawOnChartArea: false,
                            },
                        }
                    }
                }
            });
        }
        
        function updateProviderBreakdown(providers) {
            const container = document.getElementById('provider-breakdown');
            let html = '';
            
            for (const [provider, data] of Object.entries(providers)) {
                html += `
                    <div class="provider-card card">
                        <div class="card-body">
                            <h6 class="text-capitalize">${provider}</h6>
                            <small class="text-muted">
                                ${data.requests} requests<br>
                                $${data.cost.toFixed(4)} cost<br>
                                ${(data.input_tokens / 1000).toFixed(1)}K input tokens<br>
                                ${(data.output_tokens / 1000).toFixed(1)}K output tokens
                            </small>
                        </div>
                    </div>
                `;
            }
            
            container.innerHTML = html || '<p class="text-muted">No usage data available</p>';
        }
        
        function updateDailyUsage(data) {
            const container = document.getElementById('daily-usage');
            let html = '';
            
            if (Object.keys(data).length === 0) {
                html = '<p class="text-muted">No usage today</p>';
            } else {
                for (const [provider, models] of Object.entries(data)) {
                    html += `<h6 class="text-capitalize">${provider}</h6>`;
                    for (const [model, usage] of Object.entries(models)) {
                        html += `
                            <div class="row mb-2">
                                <div class="col-md-3"><code>${model}</code></div>
                                <div class="col-md-2">${usage.requests} req</div>
                                <div class="col-md-2">${(usage.input_tokens / 1000).toFixed(1)}K in</div>
                                <div class="col-md-2">${(usage.output_tokens / 1000).toFixed(1)}K out</div>
                                <div class="col-md-3">$${usage.cost.toFixed(4)}</div>
                            </div>
                        `;
                    }
                }
            }
            
            container.innerHTML = html;
        }
        
        // Load data on page load and refresh every 30 seconds
        loadUsageSummary();
        loadDailyUsage();
        setInterval(() => {
            loadUsageSummary();
            loadDailyUsage();
        }, 30000);
    </script>
</body>
</html>"""
        
        self.wfile.write(html.encode('utf-8'))
    
    def serve_usage_summary(self):
        """Serve usage summary API."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        
        summary = token_meter.get_usage_summary(days=7)
        self.wfile.write(json.dumps(summary).encode('utf-8'))
    
    def serve_daily_usage(self):
        """Serve today's usage API."""
        self.send_response(200)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.end_headers()
        
        daily = token_meter.get_daily_usage()
        self.wfile.write(json.dumps(daily).encode('utf-8'))
    
    def log_message(self, format, *args):
        pass  # Suppress logging

print("Token Usage Dashboard Starting...")
print("Available at: http://localhost:8003")

PORT = 8003
try:
    with socketserver.TCPServer(("", PORT), UsageAdminHandler) as httpd:
        httpd.serve_forever()
except KeyboardInterrupt:
    print("\\nUsage Dashboard stopped")
except Exception as e:
    print(f"Usage Dashboard error: {e}")