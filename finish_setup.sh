#!/bin/bash
# Finish the setup after fixing Pydantic issues

echo "🔧 Finishing LPE setup..."

# Activate virtual environment
source venv/bin/activate

# Install sentence-transformers
echo "📦 Installing sentence-transformers..."
pip install sentence-transformers

# Initialize database
echo "🗄️ Initializing database..."
python scripts/init_db.py

# Run tests
echo "🧪 Running setup tests..."
python test_setup.py

echo ""
echo "✅ Setup complete!"
echo ""
echo "Run the demo with:"
echo "  python demo.py"