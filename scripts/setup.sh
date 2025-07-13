#!/bin/bash
# Setup script for Lamish Projection Engine

echo "Setting up Lamish Projection Engine..."

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then 
    echo "Error: Python $required_version or higher is required (found $python_version)"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install package
echo "Installing package..."
pip install --upgrade pip
pip install -e ".[dev]"

# Copy .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cp .env.example .env
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "Warning: Docker is not installed. Please install Docker to use the database features."
else
    echo "Starting PostgreSQL with pgvector..."
    docker-compose up -d
    
    # Wait for database to be ready
    echo "Waiting for database to be ready..."
    sleep 5
fi

echo ""
echo "Setup complete! 🎉"
echo ""
echo "To get started:"
echo "  1. Activate the virtual environment: source venv/bin/activate"
echo "  2. Check system status: lpe status"
echo "  3. List available transformers: lpe list-transformers"
echo ""