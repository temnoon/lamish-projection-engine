#!/bin/bash
# Complete setup script for LPE

set -e

echo "🚀 Complete Lamish Projection Engine Setup"
echo "=========================================="

# Step 1: Setup database
echo ""
echo "Step 1: Setting up PostgreSQL database..."
./setup_database.sh

# Step 2: Activate virtual environment
echo ""
echo "Step 2: Activating virtual environment..."
source venv/bin/activate

# Step 3: Initialize database schema
echo ""
echo "Step 3: Initializing database schema..."
python scripts/init_db.py

# Step 4: Run tests
echo ""
echo "Step 4: Running tests..."
python test_setup.py

# Step 5: Success!
echo ""
echo "🎉 Setup Complete!"
echo ""
echo "You can now run:"
echo "  source venv/bin/activate"
echo "  python demo.py"
echo ""
echo "Or use the CLI:"
echo "  lpe status"
echo "  lpe project --help"
echo "  lpe explore"