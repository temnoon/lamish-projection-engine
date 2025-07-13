"""Simple configuration for testing without dependencies."""
import os
from typing import Optional

class SimpleConfig:
    """Simple configuration object."""
    
    def __init__(self):
        self.use_mock_llm = os.getenv('LPE_USE_MOCK_LLM', 'false').lower() == 'true'
        self.llm_model = os.getenv('LPE_LLM_MODEL', 'gemma3:12b')
        self.embedding_model = os.getenv('LPE_EMBEDDING_MODEL', 'nomic-embed-text')
        self.ollama_host = os.getenv('LPE_OLLAMA_HOST', 'http://localhost:11434')
        self.llm_temperature = float(os.getenv('LPE_LLM_TEMPERATURE', '0.7'))
        self.llm_max_tokens = int(os.getenv('LPE_LLM_MAX_TOKENS', '8192'))

_config = None

def get_config():
    """Get the configuration."""
    global _config
    if _config is None:
        _config = SimpleConfig()
    return _config