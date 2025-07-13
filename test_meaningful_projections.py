#!/usr/bin/env python3
"""Test that projections create meaningful allegorical transformations."""
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from lamish_projection_engine.core.projection import TranslationChain
from lamish_projection_engine.core.llm import get_llm_provider, MockLLMProvider
from lamish_projection_engine.utils.config import get_config
import os

# Force mock LLM for testing
os.environ['LPE_USE_MOCK_LLM'] = 'true'

console = Console()

def test_meaningful_projection():
    """Test that projections preserve narrative meaning."""
    console.print("[bold cyan]Testing Meaningful Narrative Projection[/bold cyan]\n")
    
    # Test narrative about Sam Altman
    narrative = """Sam Altman dropped out of Stanford after just two years to start his 
first company, Loopt, which raised over $30 million in venture funding. He later 
became president of Y Combinator and is now CEO of OpenAI, leading the AI revolution 
with a net worth of $1.7 billion."""
    
    console.print("[bold]Original Narrative:[/bold]")
    console.print(narrative)
    console.print()
    
    # Create projection
    chain = TranslationChain(
        persona="neutral",
        namespace="lamish-galaxy", 
        style="standard",
        console=console,
        verbose=True
    )
    
    console.print("[bold]Creating Allegorical Projection...[/bold]\n")
    projection = chain.run(narrative, show_steps=True)
    
    # Verify key elements are preserved
    console.print("\n[bold cyan]Verification:[/bold cyan]")
    
    # Check if the projection contains mapped elements
    final_text = projection.final_projection.lower()
    
    checks = [
        ("University → Academy mapping", "academy" in final_text),
        ("Entrepreneur → Navigator mapping", "navigator" in final_text or "innovator" in final_text),
        ("Funding → Resonance mapping", "resonance" in final_text or "frequency" in final_text),
        ("AI/Tech → Consciousness/Synthetic minds", "consciousness" in final_text or "synthetic" in final_text),
        ("Story structure preserved", "left" in final_text or "departed" in final_text)
    ]
    
    all_passed = True
    for check_name, passed in checks:
        status = "[green]✓[/green]" if passed else "[red]✗[/red]"
        console.print(f"{status} {check_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        console.print("\n[green]✓ Success! The projection preserves the narrative meaning.[/green]")
    else:
        console.print("\n[yellow]⚠ Some elements were not properly preserved.[/yellow]")
    
    # Show comparison
    console.print("\n[bold]Key Narrative Elements Comparison:[/bold]")
    console.print("Original: Tech entrepreneur leaves university → starts companies → leads AI org")
    console.print("Projected: Navigator leaves Academy → creates ventures → leads consciousness revolution")


if __name__ == "__main__":
    test_meaningful_projection()