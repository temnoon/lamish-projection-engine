#!/bin/bash
# Fix remaining issues and test

echo "🔧 Fixing and testing LPE..."

# Activate virtual environment
source venv/bin/activate

# Initialize database
echo "🗄️ Initializing database..."
python scripts/init_db.py

# Run tests
echo "🧪 Running setup tests..."
python test_setup.py

# If all good, run demo
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Everything looks good!"
    echo ""
    echo "Would you like to run the demo? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        python demo.py
    fi
else
    echo ""
    echo "⚠️ There were some issues. Check the output above."
fi