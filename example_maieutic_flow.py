#!/usr/bin/env python3
"""Example showing the complete maieutic dialogue to projection flow."""
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

console = Console()

def show_example_flow():
    """Show an example of the complete flow."""
    console.print(Panel.fit(
        "[bold cyan]Maieutic Dialogue → Allegorical Projection[/bold cyan]\n"
        "[dim]Example Flow[/dim]",
        border_style="cyan"
    ))
    
    # Example narrative
    narrative = """
    Our research team spent three years developing a breakthrough algorithm for 
    early disease detection. Just before publication, we discovered a large 
    corporation had filed patents on remarkably similar methods. We face a 
    dilemma: fight the patents and delay helping patients, or publish anyway 
    and risk legal consequences.
    """
    
    console.print("\n[bold]1. Initial Narrative:[/bold]")
    console.print(Panel(narrative.strip(), border_style="dim"))
    
    # Example dialogue
    console.print("\n[bold]2. Maieutic Dialogue:[/bold]\n")
    
    qa_pairs = [
        {
            "q": "What do you believe is at the core of your dilemma?",
            "a": "The conflict between intellectual property rights and the moral imperative to help people who are suffering.",
            "insights": ["Tension between legal ownership and moral duty", "Innovation vs. patient welfare"]
        },
        {
            "q": "What assumptions about ownership and innovation might be underlying this situation?",
            "a": "We assume that being first gives us rights, but also that knowledge that can save lives should be shared. These seem contradictory.",
            "insights": ["Question of whether life-saving knowledge can be 'owned'", "First-mover advantage vs. collective good"]
        },
        {
            "q": "If you strip away the specifics, what universal pattern or archetype does this represent?",
            "a": "It's like Prometheus stealing fire from the gods - taking something powerful and giving it to humanity, knowing there will be consequences.",
            "insights": ["Prometheus archetype: bringing knowledge at personal cost", "The price of challenging established power"]
        }
    ]
    
    for i, qa in enumerate(qa_pairs, 1):
        console.print(f"[yellow]Q{i}:[/yellow] {qa['q']}")
        console.print(f"[green]A{i}:[/green] {qa['a']}")
        console.print("[magenta]Insights:[/magenta]")
        for insight in qa['insights']:
            console.print(f"  • {insight}")
        console.print()
    
    # Emergent understanding
    console.print("[bold]3. Emergent Understanding:[/bold]")
    understanding = """
    This narrative reveals a fundamental tension between proprietary control and 
    humanitarian duty. The Promethean archetype suggests that advancing human 
    welfare often requires challenging established power structures, even at 
    personal cost. The true conflict isn't about patents but about who controls 
    access to life-saving knowledge.
    """
    console.print(Panel(understanding.strip(), border_style="cyan"))
    
    # Configuration suggestion
    console.print("\n[bold]4. Suggested Configuration:[/bold]")
    console.print("Based on the archetypal themes and moral conflict discovered:")
    config_table = Columns([
        Panel("philosopher", title="Persona", border_style="yellow"),
        Panel("quantum-realm", title="Namespace", border_style="magenta"),
        Panel("poetic", title="Style", border_style="blue")
    ])
    console.print(config_table)
    
    # Enriched projection
    console.print("\n[bold]5. Allegorical Projection:[/bold]")
    console.print("[dim]Using insights to create a more meaningful transformation...[/dim]\n")
    
    projection = """
    In the Quantum Realm, where possibilities collapse into singular realities, 
    the Observers discovered a probability wave that could predict the decay of 
    life-states before manifestation. They had woven this knowledge into elegant 
    equations, preparing to release it to all conscious entities.
    
    But the Entropy Syndicate had already claimed ownership of similar wave-forms, 
    binding them in patents of probability. The Observers faced the Prometheus 
    Paradox: release the equations and face the Syndicate's reality-lawyers, or 
    withhold them while life-states needlessly collapsed into void.
    
    In the space between ownership and obligation, between the first observation 
    and the final measurement, they contemplated: Does the act of discovering a 
    truth grant dominion over it? Or does truth, like light itself, belong to 
    all who can perceive it?
    """
    
    console.print(Panel(projection.strip(), title="[bold]Final Projection[/bold]", border_style="green"))
    
    # Reflection
    console.print("\n[bold]6. Reflection:[/bold]")
    reflection = """
    This projection through the Quantum Realm reveals how the original dilemma 
    transcends its specific context. By transforming patents into "probability 
    bindings" and disease detection into "predicting life-state decay," we see 
    the universal nature of the conflict. The Prometheus Paradox illuminates 
    that some knowledge, by its very nature, resists ownership—especially when 
    withholding it causes suffering.
    """
    console.print(Panel(reflection.strip(), border_style="magenta"))
    
    # Summary
    console.print("\n[bold green]Summary:[/bold green]")
    console.print("""
    The maieutic dialogue revealed deeper archetypal patterns (Prometheus) and 
    fundamental tensions (ownership vs. duty) that weren't explicit in the 
    original narrative. These insights informed the choice of:
    
    - [yellow]Philosopher persona[/yellow] to explore ethical dimensions
    - [magenta]Quantum realm[/magenta] to abstract ownership into probability
    - [blue]Poetic style[/blue] to capture the mythic resonance
    
    The resulting projection is richer and more universally meaningful than a 
    direct transformation would have been.
    """)


if __name__ == "__main__":
    show_example_flow()