#!/usr/bin/env python3
"""Test environment configuration loading."""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_config():
    """Test configuration loading."""
    print("Testing configuration loading...\n")
    
    # First, show raw environment
    print("Environment variables:")
    for key, value in os.environ.items():
        if key.startswith('LPE_') or key.startswith('POSTGRES_'):
            print(f"  {key}={value}")
    
    print("\n" + "-"*50 + "\n")
    
    # Load config
    from lamish_projection_engine.utils.config import get_config, reload_config
    
    # Force reload
    config = reload_config()
    
    print("Loaded configuration:")
    print(f"  LLM Model: {config.llm_model}")
    print(f"  Embedding Model: {config.embedding_model}")
    print(f"  Ollama Host: {config.ollama_host}")
    print(f"  Max Tokens: {config.llm_max_tokens}")
    print(f"  Use Mock LLM: {config.use_mock_llm}")
    
    # Test that it matches .env
    assert config.llm_model == "gemma3:12b", f"Expected gemma3:12b, got {config.llm_model}"
    assert config.llm_max_tokens == 4096, f"Expected 4096, got {config.llm_max_tokens}"
    
    print("\n✅ Configuration loaded correctly from .env!")


if __name__ == "__main__":
    test_config()