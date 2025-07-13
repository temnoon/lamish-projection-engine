#!/usr/bin/env python3
"""Debug Ollama list models issue."""
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from ollama import Client
import json

def debug_ollama():
    """Debug the Ollama client list method."""
    try:
        client = Client(host="http://localhost:11434")
        
        # Test list method
        models_response = client.list()
        print("Raw response from client.list():")
        print(f"Type: {type(models_response)}")
        print(f"Dir: {dir(models_response)}")
        
        # Try to access models
        if hasattr(models_response, 'models'):
            models = models_response.models
            print(f"\nFound models attribute: {len(models)} models")
            for model in models:
                print(f"  - {model.name}" if hasattr(model, 'name') else f"  - {model}")
        elif hasattr(models_response, 'model'):
            print(f"\nFound model attribute: {models_response.model}")
        else:
            print(f"\nNo models found. Available attributes: {[attr for attr in dir(models_response) if not attr.startswith('_')]}")
            
        # Try converting to dict if possible
        try:
            if hasattr(models_response, 'dict'):
                dict_resp = models_response.dict()
                print(f"\nAs dict: {dict_resp}")
            elif hasattr(models_response, 'model_dump'):
                dict_resp = models_response.model_dump()
                print(f"\nAs model_dump: {dict_resp}")
        except Exception as e:
            print(f"\nCouldn't convert to dict: {e}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    debug_ollama()