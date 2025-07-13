#!/bin/bash
# Install LLM dependencies

echo "📦 Installing LLM dependencies..."

# Activate virtual environment
source venv/bin/activate

# Install Ollama and LangChain packages
pip install ollama langchain langchain-ollama

echo "✅ LLM dependencies installed!"
echo ""
echo "Next steps:"
echo "1. Set up Ollama: ./setup_ollama.sh"
echo "2. Test LLM connection: python test_llm.py"