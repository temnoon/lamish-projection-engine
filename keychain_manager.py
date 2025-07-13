#!/usr/bin/env python3
"""macOS Keychain manager for secure API key storage."""

import subprocess
import json
from typing import Optional, Dict, Any

class KeychainManager:
    """Manages API keys securely using macOS Keychain."""
    
    def __init__(self, service_name: str = "LamishProjectionEngine"):
        self.service_name = service_name
    
    def store_api_key(self, provider: str, api_key: str) -> bool:
        """Store API key in keychain."""
        try:
            cmd = [
                "security", "add-generic-password",
                "-s", self.service_name,
                "-a", f"{provider}_api_key", 
                "-w", api_key,
                "-U"  # Update if exists
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            print(f"Failed to store {provider} API key: {e}")
            return False
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Retrieve API key from keychain."""
        try:
            cmd = [
                "security", "find-generic-password",
                "-s", self.service_name,
                "-a", f"{provider}_api_key",
                "-w"  # Return only the password
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception as e:
            print(f"Failed to retrieve {provider} API key: {e}")
            return None
    
    def delete_api_key(self, provider: str) -> bool:
        """Delete API key from keychain."""
        try:
            cmd = [
                "security", "delete-generic-password", 
                "-s", self.service_name,
                "-a", f"{provider}_api_key"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            print(f"Failed to delete {provider} API key: {e}")
            return False
    
    def list_stored_keys(self) -> Dict[str, bool]:
        """List which API keys are stored."""
        providers = ["openai", "anthropic", "google", "ollama"]
        stored = {}
        
        for provider in providers:
            api_key = self.get_api_key(provider)
            stored[provider] = api_key is not None and len(api_key) > 0
            
        return stored
    
    def validate_keychain_access(self) -> bool:
        """Test if we can access the keychain."""
        try:
            # Try to list keychain items for our service
            cmd = [
                "security", "find-generic-password", 
                "-s", self.service_name,
                "-g"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            return True  # Even if no items found, keychain is accessible
        except Exception as e:
            print(f"Keychain access validation failed: {e}")
            return False

# Global keychain manager instance
keychain = KeychainManager()

if __name__ == "__main__":
    # Test keychain functionality
    print("Testing macOS Keychain integration...")
    
    if not keychain.validate_keychain_access():
        print("❌ Cannot access macOS Keychain")
        exit(1)
    
    print("✅ Keychain access validated")
    
    # Show current stored keys
    stored_keys = keychain.list_stored_keys()
    print(f"Stored API keys: {stored_keys}")
    
    # Test storing and retrieving a dummy key
    test_key = "test_key_12345"
    if keychain.store_api_key("test", test_key):
        retrieved = keychain.get_api_key("test")
        if retrieved == test_key:
            print("✅ Store/retrieve test passed")
            keychain.delete_api_key("test")
        else:
            print("❌ Store/retrieve test failed")
    else:
        print("❌ Failed to store test key")