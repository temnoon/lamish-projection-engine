#!/usr/bin/env python3
"""Test Ollama connection directly."""
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from lamish_projection_engine.core.llm import OllamaProvider, get_llm_provider
from lamish_projection_engine.utils.config import get_config

def test_ollama_direct():
    """Test Ollama connection directly."""
    print("Testing Ollama connection...")
    
    # Test direct Ollama provider
    try:
        provider = OllamaProvider()
        print(f"Available: {provider.is_available()}")
        print(f"Models: {provider.list_models()}")
        
        if provider.is_available():
            # Test generation
            response = provider.generate("Hello, how are you?", "You are a helpful assistant.")
            print(f"Generation test: {response[:100]}...")
        
    except Exception as e:
        print(f"Ollama provider error: {e}")
    
    # Test config
    config = get_config()
    print(f"\nConfig:")
    print(f"  LLM Model: {config.llm_model}")
    print(f"  Embedding Model: {config.embedding_model}")
    print(f"  Use Mock: {config.use_mock_llm}")
    print(f"  Ollama Host: {config.ollama_host}")
    
    # Test provider selection
    print(f"\nProvider selection:")
    provider = get_llm_provider()
    print(f"  Provider type: {type(provider).__name__}")
    
    if hasattr(provider, 'list_models'):
        print(f"  Available models: {provider.list_models()}")


if __name__ == "__main__":
    test_ollama_direct()