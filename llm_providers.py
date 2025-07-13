#!/usr/bin/env python3
"""Unified LLM provider interface supporting OpenAI, Anthropic, Google, and Ollama."""

import json
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from keychain_manager import keychain

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.api_key = keychain.get_api_key(provider_name)
        self.available = self.api_key is not None
    
    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using the provider's API."""
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test if the provider connection is working."""
        pass
    
    def get_models(self) -> List[str]:
        """Get available models for this provider."""
        return []

class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""
    
    def __init__(self):
        super().__init__("openai")
        self.base_url = "https://api.openai.com/v1"
        self.default_model = "gpt-4"
        self.models = ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-3.5-turbo-16k"]
    
    def generate_text(self, prompt: str, model: str = None, temperature: float = 0.7, max_tokens: int = 4096) -> str:
        """Generate text using OpenAI API."""
        if not self.available:
            raise Exception("OpenAI API key not configured")
        
        model = model or self.default_model
        url = f"{self.base_url}/chat/completions"
        
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            json_data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(url, data=json_data)
            req.add_header('Content-Type', 'application/json')
            req.add_header('Authorization', f'Bearer {self.api_key}')
            
            response = urllib.request.urlopen(req, timeout=120)
            result = json.loads(response.read().decode())
            
            return result['choices'][0]['message']['content']
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def test_connection(self) -> bool:
        """Test OpenAI API connection."""
        try:
            self.generate_text("Hello", max_tokens=5)
            return True
        except:
            return False
    
    def get_models(self) -> List[str]:
        return self.models

class AnthropicProvider(LLMProvider):
    """Anthropic Claude API provider."""
    
    def __init__(self):
        super().__init__("anthropic")
        self.base_url = "https://api.anthropic.com/v1"
        self.default_model = "claude-3-sonnet-20240229"
        self.models = ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"]
    
    def generate_text(self, prompt: str, model: str = None, temperature: float = 0.7, max_tokens: int = 4096) -> str:
        """Generate text using Anthropic API."""
        if not self.available:
            raise Exception("Anthropic API key not configured")
        
        model = model or self.default_model
        url = f"{self.base_url}/messages"
        
        data = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        try:
            json_data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(url, data=json_data)
            req.add_header('Content-Type', 'application/json')
            req.add_header('Authorization', f'Bearer {self.api_key}')
            req.add_header('anthropic-version', '2023-06-01')
            
            response = urllib.request.urlopen(req, timeout=120)
            result = json.loads(response.read().decode())
            
            return result['content'][0]['text']
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")
    
    def test_connection(self) -> bool:
        """Test Anthropic API connection."""
        try:
            self.generate_text("Hello", max_tokens=5)
            return True
        except:
            return False
    
    def get_models(self) -> List[str]:
        return self.models

class GoogleProvider(LLMProvider):
    """Google Gemini API provider."""
    
    def __init__(self):
        super().__init__("google")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.default_model = "gemini-pro"
        self.models = ["gemini-pro", "gemini-pro-vision"]
    
    def generate_text(self, prompt: str, model: str = None, temperature: float = 0.7, max_tokens: int = 4096) -> str:
        """Generate text using Google Gemini API."""
        if not self.available:
            raise Exception("Google API key not configured")
        
        model = model or self.default_model
        url = f"{self.base_url}/models/{model}:generateContent?key={self.api_key}"
        
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }
        
        try:
            json_data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(url, data=json_data)
            req.add_header('Content-Type', 'application/json')
            
            response = urllib.request.urlopen(req, timeout=120)
            result = json.loads(response.read().decode())
            
            return result['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            raise Exception(f"Google API error: {str(e)}")
    
    def test_connection(self) -> bool:
        """Test Google API connection."""
        try:
            self.generate_text("Hello", max_tokens=5)
            return True
        except:
            return False
    
    def get_models(self) -> List[str]:
        return self.models

class OllamaProvider(LLMProvider):
    """Ollama local API provider."""
    
    def __init__(self):
        super().__init__("ollama")
        self.base_url = "http://localhost:11434"
        self.available = self._check_ollama_connection()
        self.models = self._get_ollama_models()
        self.default_model = "llama3.2:latest" if "llama3.2:latest" in self.models else (self.models[0] if self.models else "llama3.2:latest")
    
    def _check_ollama_connection(self) -> bool:
        """Check if Ollama is running."""
        try:
            url = f"{self.base_url}/api/tags"
            response = urllib.request.urlopen(url, timeout=5)
            return response.status == 200
        except:
            return False
    
    def _get_ollama_models(self) -> List[str]:
        """Get available Ollama models."""
        try:
            url = f"{self.base_url}/api/tags"
            response = urllib.request.urlopen(url, timeout=5)
            data = json.loads(response.read().decode())
            return [m.get('name', '') for m in data.get('models', [])]
        except:
            return []
    
    def generate_text(self, prompt: str, model: str = None, temperature: float = 0.7, max_tokens: int = 4096) -> str:
        """Generate text using Ollama API."""
        if not self.available:
            raise Exception("Ollama is not running")
        
        model = model or self.default_model
        url = f"{self.base_url}/api/generate"
        
        data = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            json_data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(url, data=json_data)
            req.add_header('Content-Type', 'application/json')
            
            response = urllib.request.urlopen(req, timeout=120)
            result = json.loads(response.read().decode())
            
            return result['response']
        except Exception as e:
            raise Exception(f"Ollama API error: {str(e)}")
    
    def test_connection(self) -> bool:
        """Test Ollama connection."""
        return self._check_ollama_connection()
    
    def get_models(self) -> List[str]:
        return self.models

class UnifiedLLMManager:
    """Manages multiple LLM providers with unified interface."""
    
    def __init__(self):
        self.providers = {
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(), 
            "google": GoogleProvider(),
            "ollama": OllamaProvider()
        }
        self.default_provider = self._get_default_provider()
    
    def _get_default_provider(self) -> str:
        """Get the first available provider as default."""
        for name, provider in self.providers.items():
            if provider.available:
                return name
        return "ollama"  # Fallback to Ollama
    
    def get_available_providers(self) -> Dict[str, bool]:
        """Get status of all providers."""
        return {name: provider.available for name, provider in self.providers.items()}
    
    def get_provider_models(self, provider_name: str) -> List[str]:
        """Get models for a specific provider."""
        if provider_name in self.providers:
            return self.providers[provider_name].get_models()
        return []
    
    def generate_text(self, prompt: str, provider: str = None, model: str = None, **kwargs) -> str:
        """Generate text using specified or default provider."""
        provider_name = provider or self.default_provider
        
        if provider_name not in self.providers:
            raise Exception(f"Unknown provider: {provider_name}")
        
        provider_obj = self.providers[provider_name]
        if not provider_obj.available:
            raise Exception(f"Provider {provider_name} is not available")
        
        return provider_obj.generate_text(prompt, model=model, **kwargs)
    
    def test_provider(self, provider_name: str) -> bool:
        """Test a specific provider."""
        if provider_name in self.providers:
            return self.providers[provider_name].test_connection()
        return False
    
    def set_api_key(self, provider_name: str, api_key: str) -> bool:
        """Set API key for a provider."""
        if keychain.store_api_key(provider_name, api_key):
            # Refresh provider instance
            if provider_name == "openai":
                self.providers[provider_name] = OpenAIProvider()
            elif provider_name == "anthropic":
                self.providers[provider_name] = AnthropicProvider()
            elif provider_name == "google":
                self.providers[provider_name] = GoogleProvider()
            return True
        return False

# Global LLM manager instance
llm_manager = UnifiedLLMManager()

if __name__ == "__main__":
    # Test the unified LLM manager
    print("Testing Unified LLM Manager...")
    
    available = llm_manager.get_available_providers()
    print(f"Available providers: {available}")
    
    for provider_name, is_available in available.items():
        if is_available:
            models = llm_manager.get_provider_models(provider_name)
            print(f"{provider_name}: {len(models)} models available")
            
            # Test with a simple prompt
            try:
                result = llm_manager.generate_text("Say hello", provider=provider_name, max_tokens=10)
                print(f"✅ {provider_name} test: {result[:50]}...")
            except Exception as e:
                print(f"❌ {provider_name} test failed: {e}")
    
    print(f"Default provider: {llm_manager.default_provider}")