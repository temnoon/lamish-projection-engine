#!/bin/bash
# Setup Ollama for LPE

echo "🤖 Setting up Ollama for Lamish Projection Engine"
echo "================================================"

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed."
    echo ""
    echo "Please install Ollama first:"
    echo "  macOS: brew install ollama"
    echo "  Linux: curl -fsSL https://ollama.ai/install.sh | sh"
    echo "  Or visit: https://ollama.ai/download"
    exit 1
fi

echo "✅ Ollama is installed"

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "🔄 Starting Ollama service..."
    ollama serve > /dev/null 2>&1 &
    sleep 5
fi

# Check again
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama service is running"
else
    echo "❌ Could not start Ollama service"
    echo "Please start it manually: ollama serve"
    exit 1
fi

# List current models
echo ""
echo "📦 Current models:"
ollama list

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -E '^LPE_' | xargs)
fi

# Use environment variables or defaults
LLM_MODEL=${LPE_LLM_MODEL:-"gemma3:12b"}
EMBEDDING_MODEL=${LPE_EMBEDDING_MODEL:-"nomic-embed-text:latest"}

echo ""
echo "📦 Models to pull:"
echo "  LLM: $LLM_MODEL"
echo "  Embeddings: $EMBEDDING_MODEL"

# Pull required models
echo ""
echo "📥 Pulling required models..."

# Pull LLM model
echo "Pulling $LLM_MODEL for text generation..."
ollama pull "$LLM_MODEL" || {
    echo "⚠️ Could not pull $LLM_MODEL"
    echo "Available models:"
    ollama list
    echo ""
    echo "Please manually pull a model with: ollama pull <model-name>"
}

# Pull embedding model
echo "Pulling $EMBEDDING_MODEL for embeddings..."
ollama pull "$EMBEDDING_MODEL" || {
    echo "⚠️ Could not pull $EMBEDDING_MODEL"
    echo "You may need to manually pull an embedding model"
}

echo ""
echo "📦 Available models after setup:"
ollama list

echo ""
echo "✅ Ollama setup complete!"
echo ""
echo "To test the LLM connection:"
echo "  source venv/bin/activate"
echo "  python -m lamish_projection_engine.core.llm"