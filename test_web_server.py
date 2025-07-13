#!/usr/bin/env python3
"""Test the web server and new features."""
import sys
from pathlib import Path
import os

# Use real LLM for better testing
# os.environ['LPE_USE_MOCK_LLM'] = 'true'

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from lamish_projection_engine.config.dynamic_attributes import ConfigurationManager, PersonaAttribute
from lamish_projection_engine.core.translation_roundtrip import LanguageRoundTripAnalyzer
from lamish_projection_engine.web.app import app
from fastapi.testclient import TestClient

console = Console()


def test_dynamic_configuration():
    """Test the dynamic configuration system."""
    console.print("[bold cyan]Testing Dynamic Configuration System[/bold cyan]\n")
    
    # Create configuration manager
    config_manager = ConfigurationManager()
    
    # Test persona configuration
    persona = config_manager.get_attribute("persona")
    console.print(f"[green]✓ Persona attribute loaded with {len(persona.fields)} fields[/green]")
    
    # Test field updates
    persona.update_field("voice_style", "analytical and precise", "test")
    console.print(f"[green]✓ Updated voice_style field[/green]")
    
    # Test system prompt generation
    prompt = config_manager.generate_system_prompt({"narrative_topic": "innovation"})
    console.print(f"[green]✓ Generated system prompt ({len(prompt)} chars)[/green]")
    
    console.print("\n[bold]Sample Generated Prompt:[/bold]")
    console.print(prompt[:300] + "..." if len(prompt) > 300 else prompt)


def test_round_trip_analysis():
    """Test the round-trip translation analysis."""
    console.print("\n[bold cyan]Testing Round-trip Translation Analysis[/bold cyan]\n")
    
    analyzer = LanguageRoundTripAnalyzer()
    
    test_text = "The young entrepreneur left university to start an innovative company."
    
    console.print(f"[dim]Testing with: {test_text}[/dim]")
    
    try:
        result = analyzer.perform_round_trip(test_text, "spanish")
        
        console.print(f"[green]✓ Round-trip analysis completed[/green]")
        console.print(f"  Semantic drift: {result.semantic_drift:.1%}")
        console.print(f"  Original: {result.original_text}")
        console.print(f"  Final: {result.final_text}")
        
    except Exception as e:
        console.print(f"[red]✗ Round-trip analysis failed: {e}[/red]")


def test_web_api():
    """Test the web API endpoints."""
    console.print("\n[bold cyan]Testing Web API[/bold cyan]\n")
    
    client = TestClient(app)
    
    # Test health endpoint
    response = client.get("/api/health")
    if response.status_code == 200:
        console.print("[green]✓ Health endpoint working[/green]")
    else:
        console.print(f"[red]✗ Health endpoint failed: {response.status_code}[/red]")
    
    # Test config endpoint
    response = client.get("/api/config")
    if response.status_code == 200:
        config = response.json()
        console.print(f"[green]✓ Config endpoint working ({len(config)} attributes)[/green]")
    else:
        console.print(f"[red]✗ Config endpoint failed: {response.status_code}[/red]")
    
    # Test projection creation
    projection_data = {
        "narrative": "A simple test narrative about innovation.",
        "show_steps": False
    }
    
    response = client.post("/api/projection/create", json=projection_data)
    if response.status_code == 200:
        projection = response.json()
        console.print("[green]✓ Projection creation working[/green]")
        console.print(f"  Final projection: {projection['final_projection'][:100]}...")
    else:
        console.print(f"[red]✗ Projection creation failed: {response.status_code}[/red]")
    
    # Test round-trip endpoint
    roundtrip_data = {
        "text": "Innovation drives progress.",
        "intermediate_language": "spanish"
    }
    
    response = client.post("/api/translation/round-trip", json=roundtrip_data)
    if response.status_code == 200:
        result = response.json()
        console.print("[green]✓ Round-trip endpoint working[/green]")
        console.print(f"  Semantic drift: {result['semantic_drift']:.1%}")
    else:
        console.print(f"[red]✗ Round-trip endpoint failed: {response.status_code}[/red]")


def test_ai_field_generation():
    """Test AI-generated field functionality."""
    console.print("\n[bold cyan]Testing AI Field Generation[/bold cyan]\n")
    
    config_manager = ConfigurationManager()
    persona = config_manager.get_attribute("persona")
    
    # Test field generation
    try:
        persona.generate_field_with_ai(
            "contextual_insight",
            "Based on the persona type '{base_type}', what contextual insight would be most valuable?",
            {"narrative_context": "technology innovation"}
        )
        
        if "contextual_insight" in persona.fields:
            console.print("[green]✓ AI field generation working[/green]")
            console.print(f"  Generated: {persona.fields['contextual_insight'].value}")
        else:
            console.print("[yellow]⚠ AI field generation completed but field not found[/yellow]")
            
    except Exception as e:
        console.print(f"[red]✗ AI field generation failed: {e}[/red]")


def main():
    """Run all tests."""
    console.print("[bold]LPE Advanced Features Test Suite[/bold]\n")
    
    test_dynamic_configuration()
    test_round_trip_analysis()
    test_ai_field_generation()
    test_web_api()
    
    console.print("\n[bold green]✓ Test suite completed![/bold green]")
    console.print("\n[bold]Next Steps:[/bold]")
    console.print("  • Run: [cyan]python -m lamish_projection_engine.cli.main web[/cyan] to start web server")
    console.print("  • Run: [cyan]python -m lamish_projection_engine.cli.main config[/cyan] for configuration")
    console.print("  • Run: [cyan]python -m lamish_projection_engine.cli.main roundtrip[/cyan] for translation analysis")


if __name__ == "__main__":
    main()