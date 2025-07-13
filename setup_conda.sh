#!/bin/bash
# Conda-specific setup script for Lamish Projection Engine

set -e  # Exit on error

echo "🚀 Setting up Lamish Projection Engine with Conda..."

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "❌ Error: Conda not found. Please install Anaconda or Miniconda."
    exit 1
fi

# Create conda environment
echo "📦 Creating conda environment 'lpe'..."
conda env create -f environment.yml -n lpe || {
    echo "Environment already exists. Updating..."
    conda env update -f environment.yml -n lpe
}

# Activate the environment
echo "🔄 Activating conda environment..."
eval "$(conda shell.bash hook)"
conda activate lpe

# Install additional pip packages that might not be in conda
echo "📚 Installing additional pip packages..."
pip install pgvector sentence-transformers

# Initialize database
echo "🗄️ Initializing database..."
python scripts/init_db.py

echo "✅ Setup complete!"
echo ""
echo "To activate the environment and run the demo:"
echo "  conda activate lpe"
echo "  python demo.py"
echo ""
echo "To use the CLI:"
echo "  python -m lamish_projection_engine.cli.main --help"