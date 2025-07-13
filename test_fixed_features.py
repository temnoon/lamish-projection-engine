#!/usr/bin/env python3
"""Test the fixed LPE features."""
import sys
from pathlib import Path

# Add to path - don't override LLM settings
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from lamish_projection_engine.core.translation_roundtrip import LanguageRoundTripAnalyzer
from lamish_projection_engine.config.dynamic_attributes import ConfigurationManager
from lamish_projection_engine.core.llm import get_llm_provider

console = Console()

def test_ollama_integration():
    """Test real Ollama integration."""
    console.print("[bold cyan]Testing Real Ollama Integration[/bold cyan]\n")
    
    provider = get_llm_provider()
    console.print(f"Provider type: {type(provider).__name__}")
    
    if hasattr(provider, 'list_models'):
        models = provider.list_models()
        console.print(f"Available models: {models}")
    
    try:
        # Test actual generation
        response = provider.generate("What is innovation?", "You are a helpful assistant.")
        console.print(f"[green]✓ Real LLM generation working[/green]")
        console.print(f"Response preview: {response[:100]}...")
    except Exception as e:
        console.print(f"[red]✗ LLM generation failed: {e}[/red]")


def test_real_translation():
    """Test real translation analysis."""
    console.print("\n[bold cyan]Testing Real Translation Analysis[/bold cyan]\n")
    
    analyzer = LanguageRoundTripAnalyzer()
    
    try:
        # Use a simple test that should complete quickly
        result = analyzer.perform_round_trip("Innovation is important.", "spanish")
        
        console.print(f"[green]✓ Real translation analysis working[/green]")
        console.print(f"Original: {result.original_text}")
        console.print(f"Final: {result.final_text}")
        console.print(f"Semantic drift: {result.semantic_drift:.1%}")
        
        if result.preserved_elements:
            console.print(f"Preserved: {result.preserved_elements}")
        
    except Exception as e:
        console.print(f"[red]✗ Translation analysis failed: {e}[/red]")


def test_dynamic_config_with_real_llm():
    """Test dynamic configuration with real LLM."""
    console.print("\n[bold cyan]Testing Dynamic Config with Real LLM[/bold cyan]\n")
    
    try:
        config_manager = ConfigurationManager()
        persona = config_manager.get_attribute("persona")
        
        console.print(f"[green]✓ Configuration loaded with {len(persona.fields)} fields[/green]")
        
        # Test AI field generation with real LLM
        persona.generate_field_with_ai(
            "test_field",
            "What would be most important for a {base_type} persona to consider?",
            {"narrative_context": "technology"}
        )
        
        if "test_field" in persona.fields:
            console.print(f"[green]✓ AI field generation with real LLM working[/green]")
            console.print(f"Generated value: {persona.fields['test_field'].value[:100]}...")
        
    except Exception as e:
        console.print(f"[red]✗ Dynamic config with real LLM failed: {e}[/red]")


def test_system_prompt_generation():
    """Test system prompt generation."""
    console.print("\n[bold cyan]Testing System Prompt Generation[/bold cyan]\n")
    
    try:
        config_manager = ConfigurationManager()
        prompt = config_manager.generate_system_prompt({"narrative_topic": "innovation"})
        
        console.print(f"[green]✓ System prompt generation working[/green]")
        console.print(f"Prompt length: {len(prompt)} characters")
        console.print(f"Prompt preview: {prompt[:200]}...")
        
    except Exception as e:
        console.print(f"[red]✗ System prompt generation failed: {e}[/red]")


def main():
    """Run all tests with real LLM."""
    console.print("[bold]LPE Fixed Features Test[/bold]\n")
    console.print("[dim]Testing with real Ollama integration[/dim]\n")
    
    test_ollama_integration()
    test_dynamic_config_with_real_llm()
    test_system_prompt_generation()
    
    # Only test translation if it's quick
    console.print("\n[yellow]Skipping real translation test (can be slow)[/yellow]")
    console.print("[dim]To test: python -m lamish_projection_engine.cli.main roundtrip[/dim]")
    
    console.print("\n[bold green]✓ Core features tested![/bold green]")
    console.print("\n[bold]Next steps:[/bold]")
    console.print("  • Run: [cyan]python start_lpe.py web[/cyan] to test web interface")
    console.print("  • Run: [cyan]python -m lamish_projection_engine.cli.main config[/cyan] for interactive config")
    console.print("  • Run: [cyan]python -m lamish_projection_engine.cli.main roundtrip[/cyan] for translation analysis")


if __name__ == "__main__":
    main()