#!/usr/bin/env python3
"""Token usage metering and cost tracking for LLM providers."""

import json
import time
from pathlib import Path
from datetime import datetime, date
from typing import Dict, List, Optional

class TokenMeter:
    """Track token usage and costs across different LLM providers."""
    
    def __init__(self):
        self.usage_file = Path.home() / ".lpe" / "token_usage.json"
        self.usage_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Current pricing per 1M tokens (as of 2024-2025)
        self.pricing = {
            "openai": {
                "gpt-4o": {"input": 2.50, "output": 10.00},
                "gpt-4o-mini": {"input": 0.15, "output": 0.60},
                "o1-preview": {"input": 15.00, "output": 60.00},
                "o1-mini": {"input": 3.00, "output": 12.00},
                "gpt-4-turbo": {"input": 10.00, "output": 30.00},
                "gpt-4": {"input": 30.00, "output": 60.00},
                "gpt-3.5-turbo": {"input": 0.50, "output": 1.50}
            },
            "anthropic": {
                "claude-3-opus-20240229": {"input": 15.00, "output": 75.00},
                "claude-3-sonnet-20240229": {"input": 3.00, "output": 15.00},
                "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25}
            },
            "google": {
                "gemini-2.5-pro": {"input": 1.25, "output": 5.00},
                "gemini-2.5-flash": {"input": 0.075, "output": 0.30},
                "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
                "gemini-1.5-flash": {"input": 0.075, "output": 0.30}
            },
            "ollama": {
                # Ollama is free (local processing)
                "default": {"input": 0.00, "output": 0.00}
            }
        }
        
        self.load_usage_data()
    
    def load_usage_data(self):
        """Load existing usage data."""
        if self.usage_file.exists():
            try:
                with open(self.usage_file, 'r') as f:
                    self.usage_data = json.load(f)
            except:
                self.usage_data = {"daily": {}, "total": {}}
        else:
            self.usage_data = {"daily": {}, "total": {}}
    
    def save_usage_data(self):
        """Save usage data to file."""
        with open(self.usage_file, 'w') as f:
            json.dump(self.usage_data, f, indent=2)
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count from text (rough approximation)."""
        # Rough estimate: ~4 characters per token for most models
        return max(1, len(text) // 4)
    
    def log_usage(self, provider: str, model: str, input_tokens: int, output_tokens: int, 
                  image_tokens: int = 0, request_type: str = "text") -> Dict:
        """Log token usage and calculate costs."""
        today = date.today().isoformat()
        timestamp = datetime.now().isoformat()
        
        # Initialize data structures if needed
        if today not in self.usage_data["daily"]:
            self.usage_data["daily"][today] = {}
        
        if provider not in self.usage_data["daily"][today]:
            self.usage_data["daily"][today][provider] = {}
        
        if model not in self.usage_data["daily"][today][provider]:
            self.usage_data["daily"][today][provider][model] = {
                "input_tokens": 0,
                "output_tokens": 0, 
                "image_tokens": 0,
                "requests": 0,
                "cost": 0.0
            }
        
        # Calculate costs
        if provider in self.pricing and model in self.pricing[provider]:
            pricing = self.pricing[provider][model]
            input_cost = (input_tokens / 1_000_000) * pricing["input"]
            output_cost = (output_tokens / 1_000_000) * pricing["output"]
            # Images are typically charged as input tokens
            image_cost = (image_tokens / 1_000_000) * pricing["input"] if image_tokens else 0
            total_cost = input_cost + output_cost + image_cost
        else:
            total_cost = 0.0
        
        # Update daily usage
        daily_model = self.usage_data["daily"][today][provider][model]
        daily_model["input_tokens"] += input_tokens
        daily_model["output_tokens"] += output_tokens
        daily_model["image_tokens"] += image_tokens
        daily_model["requests"] += 1
        daily_model["cost"] += total_cost
        
        # Update total usage
        if provider not in self.usage_data["total"]:
            self.usage_data["total"][provider] = {}
        
        if model not in self.usage_data["total"][provider]:
            self.usage_data["total"][provider][model] = {
                "input_tokens": 0,
                "output_tokens": 0,
                "image_tokens": 0,
                "requests": 0,
                "cost": 0.0
            }
        
        total_model = self.usage_data["total"][provider][model]
        total_model["input_tokens"] += input_tokens
        total_model["output_tokens"] += output_tokens
        total_model["image_tokens"] += image_tokens
        total_model["requests"] += 1
        total_model["cost"] += total_cost
        
        # Save data
        self.save_usage_data()
        
        # Return usage summary for this request
        return {
            "provider": provider,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "image_tokens": image_tokens,
            "cost": total_cost,
            "request_type": request_type,
            "timestamp": timestamp
        }
    
    def get_daily_usage(self, date_str: str = None) -> Dict:
        """Get usage for a specific date (today if none specified)."""
        if date_str is None:
            date_str = date.today().isoformat()
        
        return self.usage_data["daily"].get(date_str, {})
    
    def get_total_usage(self) -> Dict:
        """Get total cumulative usage."""
        return self.usage_data["total"]
    
    def get_usage_summary(self, days: int = 7) -> Dict:
        """Get usage summary for the last N days."""
        from datetime import datetime, timedelta
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
        
        summary = {
            "period": f"{start_date} to {end_date}",
            "total_cost": 0.0,
            "total_requests": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "by_provider": {}
        }
        
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.isoformat()
            daily_data = self.usage_data["daily"].get(date_str, {})
            
            for provider, models in daily_data.items():
                if provider not in summary["by_provider"]:
                    summary["by_provider"][provider] = {
                        "cost": 0.0,
                        "requests": 0,
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "models": {}
                    }
                
                for model, usage in models.items():
                    summary["total_cost"] += usage["cost"]
                    summary["total_requests"] += usage["requests"]
                    summary["total_input_tokens"] += usage["input_tokens"]
                    summary["total_output_tokens"] += usage["output_tokens"]
                    
                    summary["by_provider"][provider]["cost"] += usage["cost"]
                    summary["by_provider"][provider]["requests"] += usage["requests"]
                    summary["by_provider"][provider]["input_tokens"] += usage["input_tokens"]
                    summary["by_provider"][provider]["output_tokens"] += usage["output_tokens"]
                    
                    if model not in summary["by_provider"][provider]["models"]:
                        summary["by_provider"][provider]["models"][model] = {
                            "cost": 0.0, "requests": 0, "input_tokens": 0, "output_tokens": 0
                        }
                    
                    summary["by_provider"][provider]["models"][model]["cost"] += usage["cost"]
                    summary["by_provider"][provider]["models"][model]["requests"] += usage["requests"]
                    summary["by_provider"][provider]["models"][model]["input_tokens"] += usage["input_tokens"]
                    summary["by_provider"][provider]["models"][model]["output_tokens"] += usage["output_tokens"]
            
            current_date += timedelta(days=1)
        
        return summary

# Global token meter instance
token_meter = TokenMeter()

def estimate_image_tokens(image_data: str) -> int:
    """Estimate tokens for image data."""
    # Google Gemini: 1024x1024 image ≈ 1290 tokens
    # Rough estimate based on base64 length
    if not image_data:
        return 0
    
    # Estimate image size from base64 length
    # Base64 is ~1.33x larger than binary
    binary_size = len(image_data) * 0.75
    
    # Rough estimate: larger images use more tokens
    if binary_size > 500_000:  # Large image
        return 1500
    elif binary_size > 100_000:  # Medium image
        return 1000
    else:  # Small image
        return 500