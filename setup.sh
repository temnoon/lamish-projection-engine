#!/bin/bash
# Setup script for Lamish Projection Engine

set -e  # Exit on error

echo "🚀 Setting up Lamish Projection Engine..."

# Check if we're in conda base environment
if [[ "$CONDA_DEFAULT_ENV" == "base" ]]; then
    echo "⚠️  Detected conda base environment. Deactivating conda temporarily..."
    conda deactivate
fi

# Create virtual environment using system python3
echo "📦 Creating Python virtual environment..."
if command -v python3 &> /dev/null; then
    /usr/bin/python3 -m venv venv --system-site-packages
elif command -v python &> /dev/null; then
    /usr/bin/python -m venv venv --system-site-packages
else
    echo "❌ Error: Python 3 not found in system path"
    exit 1
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Verify we're in the venv
which python
python --version

# Upgrade pip
echo "⬆️ Upgrading pip..."
python -m pip install --upgrade pip

# Install requirements
echo "📚 Installing dependencies..."
python -m pip install -r requirements.txt

# Initialize database
echo "🗄️ Initializing database..."
python scripts/init_db.py

echo "✅ Setup complete!"
echo ""
echo "To activate the environment and run the demo:"
echo "  source venv/bin/activate"
echo "  python demo.py"
echo ""
echo "To use the CLI:"
echo "  python -m lamish_projection_engine.cli.main --help"