#!/usr/bin/env python3
"""Simple startup script for LPE with different modes."""
import sys
import os
from pathlib import Path

# Use real LLM by default - don't override environment
# os.environ['LPE_USE_MOCK_LLM'] = 'true'

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    if len(sys.argv) < 2:
        print("Usage: python start_lpe.py [web|config|test|roundtrip]")
        print()
        print("Options:")
        print("  web      - Start web server at http://localhost:8000")
        print("  config   - Configure attributes interactively")
        print("  test     - Run feature tests")
        print("  roundtrip- Test translation analysis")
        return
    
    mode = sys.argv[1].lower()
    
    if mode == "web":
        print("Starting LPE Web Server...")
        print("Will be available at: http://localhost:8000")
        print("Press Ctrl+C to stop")
        print()
        
        from lamish_projection_engine.web.app import app
        import uvicorn
        uvicorn.run(app, host="localhost", port=8000)
        
    elif mode == "config":
        print("Starting LPE Configuration Manager...")
        print()
        
        from rich.console import Console
        from lamish_projection_engine.config.dynamic_attributes import ConfigurationManager
        
        console = Console()
        config_manager = ConfigurationManager()
        
        # Show current config
        console.print("[bold]Current Configuration:[/bold]")
        for name, attr in config_manager.attributes.items():
            console.print(f"\n[cyan]{name.title()}:[/cyan]")
            for field_name, field in attr.fields.items():
                console.print(f"  {field_name}: [yellow]{field.value}[/yellow]")
        
        print("\nFor interactive editing, use: python -m lamish_projection_engine.cli.main config")
        
    elif mode == "test":
        print("Running LPE Feature Tests...")
        print()
        
        import test_web_server
        test_web_server.main()
        
    elif mode == "roundtrip":
        print("Testing Round-trip Translation...")
        print()
        
        from lamish_projection_engine.core.translation_roundtrip import LanguageRoundTripAnalyzer
        
        analyzer = LanguageRoundTripAnalyzer()
        result = analyzer.perform_round_trip(
            "Innovation drives technological progress", 
            "spanish"
        )
        
        print(f"Original: {result.original_text}")
        print(f"Final: {result.final_text}")
        print(f"Semantic drift: {result.semantic_drift:.1%}")
        
    else:
        print(f"Unknown mode: {mode}")
        print("Use: web, config, test, or roundtrip")

if __name__ == "__main__":
    main()