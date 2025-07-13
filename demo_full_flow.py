#!/usr/bin/env python3
"""Demonstrate the full maieutic dialogue to projection flow."""
import sys
from pathlib import Path
import os

# Force mock LLM for demo
os.environ['LPE_USE_MOCK_LLM'] = 'true'

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from lamish_projection_engine.core.maieutic import MaieuticDialogue, DialogueTurn, MaieuticSession
from lamish_projection_engine.core.projection import TranslationChain

console = Console()

def demo_full_flow():
    """Demonstrate the complete maieutic to projection flow."""
    console.print("[bold cyan]Lamish Projection Engine Demo[/bold cyan]")
    console.print("[dim]Maieutic Dialogue → Allegorical Projection[/dim]\n")
    
    # Original narrative
    narrative = "Sam Altman dropped out of Stanford after two years to found Loopt, which raised $30M. He later led Y Combinator and now runs OpenAI."
    
    console.print("[bold]Original Narrative:[/bold]")
    console.print(narrative)
    console.print()
    
    # Create dialogue system
    dialogue = MaieuticDialogue(console)
    session = dialogue.start_session(narrative, "understand")
    
    # Simulate maieutic dialogue
    console.print("[bold cyan]Simulating Maieutic Dialogue...[/bold cyan]\n")
    
    # Turn 1
    turn1 = DialogueTurn(
        question="What is at the heart of this narrative?",
        answer="It's about choosing personal vision over institutional path - leaving Stanford to pursue entrepreneurship.",
        insights=["Individual vision vs institutional expectations", "Courage to forge independent path"],
        depth_level=0
    )
    session.turns.append(turn1)
    console.print(f"[yellow]Q1:[/yellow] {turn1.question}")
    console.print(f"[green]A1:[/green] {turn1.answer}")
    console.print(f"[magenta]Insights:[/magenta] {', '.join(turn1.insights)}\n")
    
    # Turn 2
    turn2 = DialogueTurn(
        question="What motivated this decision to leave?",
        answer="The belief that building something new was more valuable than completing a traditional education.",
        insights=["Innovation requires breaking from tradition", "Value creation outside established systems"],
        depth_level=1
    )
    session.turns.append(turn2)
    console.print(f"[yellow]Q2:[/yellow] {turn2.question}")
    console.print(f"[green]A2:[/green] {turn2.answer}")
    console.print(f"[magenta]Insights:[/magenta] {', '.join(turn2.insights)}\n")
    
    # Turn 3
    turn3 = DialogueTurn(
        question="What does the success that followed reveal?",
        answer="That unconventional paths can lead to transformative impact - from startup to leading AI revolution.",
        insights=["Validation of non-traditional approaches", "Individual impact on technological progress"],
        depth_level=2
    )
    session.turns.append(turn3)
    console.print(f"[yellow]Q3:[/yellow] {turn3.question}")
    console.print(f"[green]A3:[/green] {turn3.answer}")
    console.print(f"[magenta]Insights:[/magenta] {', '.join(turn3.insights)}\n")
    
    # Synthesize understanding
    session.final_understanding = dialogue.synthesize_understanding()
    
    console.print("[bold]Synthesized Understanding:[/bold]")
    console.print(session.final_understanding)
    console.print()
    
    # Create enriched narrative
    console.print("[bold cyan]Creating Enriched Narrative for Projection...[/bold cyan]\n")
    enriched = dialogue._create_enriched_narrative()
    console.print("[dim]Enriched narrative incorporates dialogue insights...[/dim]\n")
    
    # Suggest configuration
    persona, namespace, style = dialogue._suggest_configuration()
    console.print(f"[bold]Suggested Configuration:[/bold]")
    console.print(f"  Persona: [yellow]{persona}[/yellow]")
    console.print(f"  Namespace: [magenta]{namespace}[/magenta]")
    console.print(f"  Style: [blue]{style}[/blue]\n")
    
    # Create projection with enriched narrative
    console.print("[bold cyan]Creating Allegorical Projection...[/bold cyan]\n")
    
    chain = TranslationChain(persona, namespace, style, console, verbose=False)
    projection = chain.run(enriched, show_steps=False)
    
    # Display final projection
    console.print("[bold]Final Allegorical Projection:[/bold]")
    console.print(projection.final_projection)
    console.print()
    
    # Display reflection
    console.print("[bold]Reflection:[/bold]")
    console.print(projection.reflection)
    console.print()
    
    # Summary
    console.print("[bold green]✓ Complete Flow Demonstrated![/bold green]")
    console.print("\nThe system successfully:")
    console.print("1. Conducted maieutic dialogue to extract deeper insights")
    console.print("2. Synthesized understanding from the Q&A process")
    console.print("3. Created an enriched narrative with key elements to preserve")
    console.print("4. Suggested appropriate configuration based on insights")
    console.print("5. Generated meaningful allegorical projection preserving the story")


if __name__ == "__main__":
    demo_full_flow()