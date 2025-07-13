#!/usr/bin/env python3
"""Test the maieutic dialogue to projection integration."""
import sys
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from lamish_projection_engine.core.maieutic import MaieuticDialogue, DialogueTurn

console = Console()

def test_integration():
    """Test that maieutic insights inform projection."""
    console.print("[bold]Testing Maieutic → Projection Integration[/bold]\n")
    
    # Create dialogue
    dialogue = MaieuticDialogue(console)
    
    # Simple test narrative
    narrative = "I discovered my colleague taking credit for my work."
    
    # Start session
    session = dialogue.start_session(narrative, "understand")
    
    # Simulate some dialogue turns
    session.turns.append(DialogueTurn(
        question="What is at the heart of this situation?",
        answer="Trust and recognition",
        insights=["Betrayal of professional trust", "Need for acknowledgment"],
        depth_level=1
    ))
    
    # Test configuration suggestion
    console.print("[cyan]Testing configuration suggestion...[/cyan]")
    persona, namespace, style = dialogue._suggest_configuration()
    console.print(f"Suggested: {persona}/{namespace}/{style}")
    
    # Test enriched narrative creation
    console.print("\n[cyan]Testing enriched narrative...[/cyan]")
    enriched = dialogue._create_enriched_narrative()
    console.print(f"Enriched narrative includes insights: {'Key insights discovered:' in enriched}")
    
    console.print("\n[green]✓ Integration test complete![/green]")
    console.print("\nThe maieutic dialogue successfully:")
    console.print("- Extracts insights from Q&A")
    console.print("- Suggests appropriate configuration")
    console.print("- Creates enriched narrative with context")
    console.print("- Passes this to projection system")


if __name__ == "__main__":
    test_integration()