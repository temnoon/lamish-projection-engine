#!/usr/bin/env python3
"""Granular model configuration for different LLM tasks."""

import json
from pathlib import Path
from typing import Dict, List, Optional

class TaskModelConfig:
    """Manages model selection for specific tasks."""
    
    def __init__(self):
        self.config_file = Path.home() / ".lpe" / "task_model_config.json"
        self.config_file.parent.mkdir(exist_ok=True)
        self.config = self.load_config()
    
    def load_config(self) -> Dict:
        """Load task-specific model configuration."""
        default_config = {
            "projection": {
                "provider": "google",
                "model": "gemini-1.5-flash",
                "temperature": 0.7,
                "max_tokens": 4096
            },
            "translation": {
                "provider": "google", 
                "model": "gemini-1.5-flash",
                "temperature": 0.3,
                "max_tokens": 4096
            },
            "maieutic": {
                "provider": "google",
                "model": "gemini-1.5-flash", 
                "temperature": 0.8,
                "max_tokens": 4096
            },
            "vision_transcription": {
                "provider": "google",
                "model": "gemini-2.5-pro",
                "temperature": 0.1,
                "max_tokens": 4096
            },
            "vision_analysis": {
                "provider": "google",
                "model": "gemini-2.5-pro",
                "temperature": 0.7,
                "max_tokens": 4096
            },
            "image_generation": {
                "local_provider": "ollamadiffuser",
                "local_model": "flux.1-schnell",
                "cloud_provider": "openai",
                "cloud_model": "dall-e-3",
                "default_provider": "openai",
                "size": "1024x1024"
            }
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    saved_config = json.load(f)
                    # Merge with defaults to ensure all tasks are covered
                    for task, config in default_config.items():
                        if task not in saved_config:
                            saved_config[task] = config
                        else:
                            # Ensure all required keys exist
                            for key, value in config.items():
                                if key not in saved_config[task]:
                                    saved_config[task][key] = value
                    return saved_config
            except:
                pass
        
        return default_config
    
    def save_config(self):
        """Save configuration to file."""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get_task_config(self, task: str) -> Dict:
        """Get configuration for a specific task."""
        return self.config.get(task, {})
    
    def update_task_config(self, task: str, config: Dict):
        """Update configuration for a specific task."""
        if task in self.config:
            self.config[task].update(config)
        else:
            self.config[task] = config
        self.save_config()
    
    def get_available_tasks(self) -> List[str]:
        """Get list of configurable tasks."""
        return list(self.config.keys())
    
    def get_task_display_name(self, task: str) -> str:
        """Get human-readable task name."""
        task_names = {
            "projection": "Allegorical Projection",
            "translation": "Round-trip Translation", 
            "maieutic": "Maieutic Dialogue",
            "vision_transcription": "Vision Transcription",
            "vision_analysis": "Vision Analysis & Redraw",
            "image_generation": "Image Generation"
        }
        return task_names.get(task, task.title())

# Global instance
task_model_config = TaskModelConfig()

if __name__ == "__main__":
    # Test the configuration
    config = TaskModelConfig()
    print("Available tasks:")
    for task in config.get_available_tasks():
        print(f"  {config.get_task_display_name(task)}: {config.get_task_config(task)}")