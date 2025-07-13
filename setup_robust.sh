#!/bin/bash
# Robust setup script that finds a working Python installation

set -e

echo "🔍 Finding a Python with working SSL support..."

# Function to test Python SSL support
test_python_ssl() {
    local python_path=$1
    if [ -f "$python_path" ]; then
        if $python_path -c "import ssl" 2>/dev/null; then
            echo "✅ Found working Python: $python_path"
            echo "   Version: $($python_path --version 2>&1)"
            return 0
        fi
    fi
    return 1
}

# Try different Python installations
PYTHON_CMD=""

# Try system Python first
if test_python_ssl "/usr/bin/python3"; then
    PYTHON_CMD="/usr/bin/python3"
# Try Homebrew Python (Intel)
elif test_python_ssl "/usr/local/bin/python3"; then
    PYTHON_CMD="/usr/local/bin/python3"
# Try Homebrew Python (Apple Silicon)
elif test_python_ssl "/opt/homebrew/bin/python3"; then
    PYTHON_CMD="/opt/homebrew/bin/python3"
# Try any python3 in PATH
elif command -v python3 &> /dev/null && test_python_ssl "$(command -v python3)"; then
    PYTHON_CMD="$(command -v python3)"
else
    echo "❌ Error: No Python installation with SSL support found!"
    echo ""
    echo "Please install Python with SSL support. Options:"
    echo "1. Install Python from python.org"
    echo "2. Install Python via Homebrew: brew install python@3.10"
    echo "3. Fix your conda installation's SSL module"
    exit 1
fi

echo ""
echo "🚀 Setting up Lamish Projection Engine..."

# Clean up any existing venv
if [ -d "venv" ]; then
    echo "🧹 Removing existing virtual environment..."
    rm -rf venv
fi

# Create virtual environment
echo "📦 Creating virtual environment with $PYTHON_CMD..."
$PYTHON_CMD -m venv venv

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Verify activation
echo "✓ Using Python: $(which python)"
echo "✓ Python version: $(python --version)"

# Upgrade pip
echo "⬆️ Upgrading pip..."
python -m pip install --upgrade pip

# Install wheel first (helps with some packages)
echo "📦 Installing wheel..."
python -m pip install wheel

# Install requirements
echo "📚 Installing dependencies..."
python -m pip install -r requirements.txt

# Initialize database
echo "🗄️ Initializing database..."
python scripts/init_db.py

# Run tests
echo "🧪 Running setup tests..."
python test_setup.py

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start using LPE:"
echo "  source venv/bin/activate"
echo "  python demo.py"
echo ""
echo "Or use the Makefile commands:"
echo "  make demo"
echo "  make test"