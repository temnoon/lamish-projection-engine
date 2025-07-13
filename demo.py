#!/usr/bin/env python3
"""Demo script for the Lamish Projection Engine."""
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
import time

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from lamish_projection_engine.cli.commands import ProjectionCLI

console = Console()

# Sample narratives for demonstration
SAMPLE_NARRATIVES = [
    {
        "title": "Corporate Conflict",
        "text": """The board meeting erupted into chaos as the CEO revealed the merger plans. 
        Shareholders were divided - some saw opportunity for growth, while others feared 
        losing the company's soul. Years of tradition hung in the balance as profit 
        margins clashed with founding principles.""",
        "persona": "critic",
        "namespace": "lamish-galaxy",
        "style": "standard"
    },
    {
        "title": "Environmental Dilemma", 
        "text": """The town faced an impossible choice: accept the factory that would bring 
        jobs but pollute the river, or preserve their pristine environment while watching 
        young families leave for opportunities elsewhere. The mayor stood at the podium, 
        knowing that either decision would define the community for generations.""",
        "persona": "philosopher",
        "namespace": "natural-world",
        "style": "poetic"
    },
    {
        "title": "Digital Privacy",
        "text": """Sarah discovered her personal data had been harvested by countless apps. 
        Each convenience came with invisible strings attached - location tracking, behavior 
        analysis, preference prediction. She wondered if true privacy was now just a 
        nostalgic concept from a pre-digital age.""",
        "persona": "storyteller",
        "namespace": "quantum-realm",
        "style": "technical"
    }
]


def run_demo():
    """Run the LPE demonstration."""
    console.print(Panel.fit(
        "[bold cyan]Lamish Projection Engine Demo[/bold cyan]\n"
        "[dim]Watch as real-world narratives transform into allegorical projections[/dim]",
        border_style="cyan"
    ))
    
    # Initialize CLI handler
    cli_handler = ProjectionCLI(console)
    
    # Check database
    console.print("\n[cyan]Checking system status...[/cyan]")
    try:
        cli_handler.initialize_database()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return
    
    console.print("\n[bold]Select a demo narrative:[/bold]")
    for i, sample in enumerate(SAMPLE_NARRATIVES, 1):
        console.print(f"{i}. {sample['title']}")
    
    # Get user choice
    while True:
        choice = console.input("\n[cyan]Enter your choice (1-3) or 'q' to quit: [/cyan]")
        if choice.lower() == 'q':
            console.print("[yellow]Demo ended.[/yellow]")
            return
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(SAMPLE_NARRATIVES):
                break
            else:
                console.print("[red]Invalid choice. Please enter 1-3.[/red]")
        except ValueError:
            console.print("[red]Invalid input. Please enter a number.[/red]")
    
    # Run the projection
    sample = SAMPLE_NARRATIVES[idx]
    
    console.print(f"\n[bold]Processing: {sample['title']}[/bold]")
    console.print(Panel(sample['text'], title="Original Narrative", border_style="blue"))
    
    console.print(f"\n[cyan]Configuration:[/cyan]")
    console.print(f"  Persona: [yellow]{sample['persona']}[/yellow]")
    console.print(f"  Namespace: [magenta]{sample['namespace']}[/magenta]")
    console.print(f"  Style: [blue]{sample['style']}[/blue]")
    
    # Create projection
    projection = cli_handler.project_narrative(
        narrative=sample['text'],
        persona=sample['persona'],
        namespace=sample['namespace'],
        style=sample['style'],
        interactive=False,
        show_steps=True
    )
    
    if projection:
        # Show recent projections
        console.print("\n[cyan]Recent projections in database:[/cyan]")
        cli_handler.list_recent_projections(limit=5)
        
        # Offer to explore
        if console.input("\n[cyan]Would you like to explore projections? (y/n): [/cyan]").lower() == 'y':
            query = console.input("[cyan]Enter search term: [/cyan]")
            cli_handler.search_projections(query)


if __name__ == "__main__":
    try:
        run_demo()
    except KeyboardInterrupt:
        console.print("\n[yellow]Demo interrupted.[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()