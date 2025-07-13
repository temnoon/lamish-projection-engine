#!/usr/bin/env python3
"""Test Google Vision API directly."""

import sys
import os
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from llm_providers import llm_manager

def test_google_vision():
    """Test Google Vision API."""
    print("Testing Google Vision API...")
    
    # Get Google provider
    google_provider = llm_manager.get_provider('google')
    
    if not google_provider:
        print("❌ Google provider not found")
        return
    
    print(f"✅ Google provider found")
    print(f"Available: {google_provider.available}")
    print(f"Base URL: {google_provider.base_url}")
    print(f"Models: {google_provider.models}")
    print(f"Vision models: {google_provider.vision_models}")
    
    if not google_provider.available:
        print("❌ Google provider not available (API key issue?)")
        return
    
    # Test simple text generation first
    try:
        print("\n📝 Testing text generation with Gemini 2.5 Pro...")
        result = google_provider.generate_text("Please say hello and tell me about Gemini 2.5 Pro", model="gemini-2.5-pro", max_tokens=50)
        print(f"✅ Text generation successful: {result}")
    except Exception as e:
        print(f"❌ Text generation failed: {e}")
        return
    
    # Test vision model availability
    print(f"\n👁️ Testing vision models...")
    for model in google_provider.vision_models:
        try:
            print(f"Testing {model}...")
            # Test without image first
            result = google_provider.generate_text("Hello", model=model, max_tokens=5)
            print(f"✅ {model} works: {result}")
        except Exception as e:
            print(f"❌ {model} failed: {e}")

if __name__ == "__main__":
    test_google_vision()