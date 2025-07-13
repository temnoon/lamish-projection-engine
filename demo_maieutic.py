#!/usr/bin/env python3
"""Demo script for maieutic dialogue."""
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

from lamish_projection_engine.core.maieutic import MaieuticDialogue

console = Console()

# Sample narratives for demonstration
SAMPLE_NARRATIVES = [
    {
        "title": "The Startup Dilemma",
        "text": """Our small team had spent two years building an innovative app that helped 
people track their carbon footprint. Just as we were gaining traction, a major tech 
company announced a nearly identical feature integrated into their ecosystem. We faced 
a choice: pivot to something new, try to compete, or look for an acquisition."""
    },
    {
        "title": "The Family Decision", 
        "text": """My elderly parents insist on staying in their large family home, despite 
mobility issues and isolation from family. They see it as their life's achievement 
and repository of memories. We worry about their safety and well-being, but they 
view any suggestion of moving as an attack on their independence."""
    },
    {
        "title": "The Creative Block",
        "text": """I've been writing the same novel for five years, constantly revising but 
never finishing. Each time I near the end, I find fundamental flaws that seem to 
require starting over. Friends say I'm being perfectionist, but I feel like I'm 
betraying the story if I don't get it right."""
    }
]


def run_demo():
    """Run the maieutic dialogue demo."""
    console.print(Panel.fit(
        "[bold cyan]Maieutic Dialogue Demo[/bold cyan]\n"
        "[dim]Explore narratives through Socratic questioning[/dim]",
        border_style="cyan"
    ))
    
    console.print("\n[bold]What is Maieutic Dialogue?[/bold]")
    console.print("""
The maieutic method (from Greek 'midwifery') uses careful questioning to help 
you discover insights that are already within you. Rather than providing answers, 
the system asks questions that guide you to deeper understanding.
    """)
    
    console.print("\n[bold]Select a sample narrative:[/bold]")
    for i, sample in enumerate(SAMPLE_NARRATIVES, 1):
        console.print(f"{i}. {sample['title']}")
    console.print(f"{len(SAMPLE_NARRATIVES) + 1}. Enter your own narrative")
    
    choice = Prompt.ask(
        "\n[cyan]Your choice[/cyan]",
        choices=[str(i) for i in range(1, len(SAMPLE_NARRATIVES) + 2)],
        default="1"
    )
    
    choice_idx = int(choice) - 1
    
    if choice_idx < len(SAMPLE_NARRATIVES):
        narrative = SAMPLE_NARRATIVES[choice_idx]['text']
        console.print(f"\n[bold]Selected: {SAMPLE_NARRATIVES[choice_idx]['title']}[/bold]")
    else:
        console.print("\n[yellow]Enter your narrative:[/yellow]")
        narrative = Prompt.ask("[green]Narrative[/green]")
    
    # Choose number of rounds
    max_turns = int(Prompt.ask(
        "\n[cyan]How many rounds of questioning?[/cyan]",
        choices=["3", "5", "7"],
        default="5"
    ))
    
    # Run dialogue
    console.print("\n[bold]Starting Maieutic Dialogue...[/bold]")
    console.print("[dim]The system will ask questions to help you explore deeper meanings.[/dim]\n")
    
    dialogue = MaieuticDialogue(console)
    dialogue.start_session(narrative, goal="discover")
    
    try:
        # The dialogue will automatically offer projection after completion
        session = dialogue.conduct_dialogue(max_turns, auto_project=True)
        
        # Offer to save
        if Confirm.ask("\n[cyan]Would you like to save this dialogue session?[/cyan]"):
            from datetime import datetime
            filename = f"maieutic_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            dialogue.save_session(filename)
            
        console.print("\n[bold green]Demo Complete![/bold green]")
        console.print("\nThe maieutic dialogue helped uncover deeper insights, which were then")
        console.print("used to create a more meaningful allegorical projection.")
            
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Dialogue interrupted.[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_demo()