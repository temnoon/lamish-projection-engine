#!/bin/bash

echo "🚀 Starting Lamish Projection Engine"
echo "===================================="

# Function to check if port is in use
check_port() {
    lsof -i :$1 >/dev/null 2>&1
}

# Function to start a service if port is free
start_service() {
    local port=$1
    local script=$2
    local name=$3
    
    if check_port $port; then
        echo "⚠️  Port $port already in use, skipping $name"
    else
        echo "🟢 Starting $name on port $port..."
        python3 "$script" &
        sleep 2
    fi
}

# Kill any existing processes (optional)
if [ "$1" = "--restart" ]; then
    echo "🔄 Stopping existing services..."
    pkill -f "immediate_interface.py"
    pkill -f "admin_server.py" 
    pkill -f "multi_llm_admin.py"
    sleep 2
fi

# Start services
start_service 8000 "immediate_interface.py" "User Interface"
start_service 8001 "admin_server.py" "Job Admin" 
start_service 8002 "multi_llm_admin.py" "Multi-Provider LLM Admin"

echo ""
echo "✅ LPE Services Started!"
echo "========================"
echo "🌐 User Interface:     http://localhost:8000"
echo "📊 Job Admin:          http://localhost:8001" 
echo "🔧 LLM Admin:          http://localhost:8002"
echo ""
echo "📋 Available LLM Providers:"

# Show available providers
python3 -c "
from llm_providers import llm_manager
providers = llm_manager.get_available_providers()
for name, available in providers.items():
    status = '✅' if available else '❌'
    print(f'   {status} {name.title()}')
"

echo ""
echo "🔐 To add API keys for cloud providers:"
echo "   1. Open http://localhost:8002"
echo "   2. Enter your API keys (stored securely in macOS Keychain)"
echo "   3. Test connections and configure models"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for user input
trap 'echo -e "\n🛑 Stopping services..."; pkill -f "immediate_interface.py"; pkill -f "admin_server.py"; pkill -f "multi_llm_admin.py"; exit 0' INT

# Keep script running
while true; do
    sleep 1
done