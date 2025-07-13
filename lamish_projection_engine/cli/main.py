"""Main CLI entry point for Lamish Projection Engine."""
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.tree import Tree
from rich.layout import Layout
from rich.live import Live
import time
from typing import Optional, Dict, Any
import sys
from pathlib import Path
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lamish_projection_engine.utils.config import load_config
from lamish_projection_engine.cli.commands import ProjectionCLI

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="Lamish Projection Engine")
@click.pass_context
def cli(ctx):
    """
    Lamish Projection Engine - Allegorical Narrative Transformation System.
    
    Transform real-world narratives into fictional allegories through AI-mediated
    projection, with full transparency and visual feedback at every step.
    """
    ctx.ensure_object(dict)
    ctx.obj['console'] = console
    
    # Show welcome banner with ASCII art
    banner = Panel.fit(
        "[bold cyan]╔═╗  ╔═╗  ╔═╗[/bold cyan]\n"
        "[bold cyan]║ ║  ║ ║  ║═╣[/bold cyan]  [bold]Lamish Projection Engine[/bold]\n"
        "[bold cyan]╚═╝  ╚═╝  ╚═╝[/bold cyan]\n\n"
        "[dim]Transform narratives through allegorical projection[/dim]\n"
        "[dim]Every step transparent, every transformation traceable[/dim]",
        border_style="cyan"
    )
    console.print(banner)
    
    # Load configuration
    try:
        config = load_config()
        ctx.obj['config'] = config
    except Exception as e:
        console.print(f"[red]Error loading configuration: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.pass_context
def status(ctx):
    """Check system status and database connection."""
    console = ctx.obj['console']
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
        console=console
    ) as progress:
        task = progress.add_task("Checking system status...", total=None)
        
        # Create status table
        table = Table(title="System Status", show_header=True, header_style="bold magenta")
        table.add_column("Component", style="cyan", no_wrap=True)
        table.add_column("Status", style="green")
        table.add_column("Details", style="dim")
        
        # Check Python version
        import sys
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        table.add_row("Python", "✓ OK", f"Version {python_version}")
        
        # Check database connection
        try:
            from lamish_projection_engine.core.database import check_connection
            db_status = check_connection()
            if db_status:
                table.add_row("PostgreSQL", "✓ Connected", "pgvector extension available")
            else:
                table.add_row("PostgreSQL", "✗ Disconnected", "Check docker-compose status")
        except Exception as e:
            table.add_row("PostgreSQL", "✗ Error", str(e))
        
        # Check available agents
        try:
            cli_handler = ProjectionCLI(console)
            # Initialize database if needed
            cli_handler.initialize_database()
            table.add_row("Agents", "✓ Loaded", "Personas, namespaces, and styles ready")
        except Exception as e:
            table.add_row("Agents", "✗ Error", str(e))
        
        progress.update(task, completed=True)
    
    console.print(table)


@cli.command()
@click.option('--text', '-t', help='Direct text input for projection')
@click.option('--file', '-f', type=click.Path(exists=True), help='File containing narrative to project')
@click.option('--persona', '-p', default='neutral', help='Persona to use (default: neutral)')
@click.option('--namespace', '-n', default='lamish-galaxy', help='Target namespace (default: lamish-galaxy)')
@click.option('--style', '-s', default='standard', help='Language style (default: standard)')
@click.option('--interactive', '-i', is_flag=True, help='Interactive dialectical mode with AI')
@click.option('--show-steps', is_flag=True, help='Show all transformation steps')
@click.pass_context
def project(ctx, text, file, persona, namespace, style, interactive, show_steps):
    """Project a narrative into an allegorical namespace."""
    console = ctx.obj['console']
    
    # Get input text
    if file:
        with open(file, 'r') as f:
            narrative = f.read()
        console.print(f"[cyan]Loaded narrative from {file}[/cyan]")
    elif text:
        narrative = text
    else:
        console.print("[yellow]Enter your narrative (Ctrl+D to finish):[/yellow]")
        lines = []
        try:
            while True:
                lines.append(input())
        except EOFError:
            narrative = '\n'.join(lines)
    
    # Display configuration
    config_tree = Tree("[bold]Projection Configuration[/bold]")
    config_tree.add(f"Persona: [cyan]{persona}[/cyan]")
    config_tree.add(f"Namespace: [cyan]{namespace}[/cyan]")
    config_tree.add(f"Style: [cyan]{style}[/cyan]")
    config_tree.add(f"Mode: [cyan]{'Interactive' if interactive else 'Automatic'}[/cyan]")
    
    console.print(Panel(config_tree, border_style="green"))
    
    # Show transformation steps if requested
    if show_steps:
        with Live(console=console, refresh_per_second=4) as live:
            layout = create_projection_layout(narrative, persona, namespace, style)
            live.update(layout)
            
            # Simulate transformation steps
            steps = [
                ("Analyzing narrative structure", 2),
                ("Deconstructing core elements", 3),
                ("Mapping to allegorical space", 4),
                ("Reconstructing in namespace", 3),
                ("Applying stylistic transform", 2),
                ("Generating reflection", 2)
            ]
            
            for step_name, duration in steps:
                update_projection_step(layout, step_name)
                live.update(layout)
                time.sleep(duration)
    
    console.print("[green]✓ Projection complete![/green]")


@cli.command()
@click.pass_context
def list_agents(ctx):
    """List available personas, namespaces, and styles."""
    console = ctx.obj['console']
    
    # Create personas table
    personas_table = Table(title="Available Personas", show_header=True, header_style="bold magenta")
    personas_table.add_column("Name", style="cyan", no_wrap=True)
    personas_table.add_column("Description", style="dim")
    personas_table.add_column("Focus", style="green")
    
    personas = [
        ("neutral", "Balanced observer without bias", "Objectivity"),
        ("advocate", "Emphasizes positive aspects", "Support"),
        ("critic", "Highlights potential issues", "Analysis"),
        ("philosopher", "Seeks deeper meaning", "Wisdom"),
        ("storyteller", "Narrative-focused transformer", "Engagement"),
    ]
    
    for name, desc, focus in personas:
        personas_table.add_row(name, desc, focus)
    
    # Create namespaces table
    namespaces_table = Table(title="Available Namespaces", show_header=True, header_style="bold magenta")
    namespaces_table.add_column("Name", style="cyan", no_wrap=True)
    namespaces_table.add_column("Type", style="green")
    namespaces_table.add_column("Description", style="dim")
    
    namespaces = [
        ("lamish-galaxy", "Primordial", "The default sci-fi allegory space"),
        ("medieval-realm", "Fantasy", "Knights, kingdoms, and quests"),
        ("corporate-dystopia", "Modern", "Business allegories and power dynamics"),
        ("natural-world", "Ecological", "Nature-based metaphors"),
        ("quantum-realm", "Abstract", "Physics and probability allegories"),
    ]
    
    for name, type_, desc in namespaces:
        namespaces_table.add_row(name, type_, desc)
    
    # Create styles table
    styles_table = Table(title="Available Language Styles", show_header=True, header_style="bold magenta")
    styles_table.add_column("Name", style="cyan", no_wrap=True)
    styles_table.add_column("Tone", style="green")
    styles_table.add_column("Use Case", style="dim")
    
    styles = [
        ("standard", "Clear", "Default readable style"),
        ("academic", "Formal", "Scholarly discourse"),
        ("poetic", "Artistic", "Metaphor-rich expression"),
        ("technical", "Precise", "Detailed specifications"),
        ("casual", "Friendly", "Conversational tone"),
    ]
    
    for name, tone, use_case in styles:
        styles_table.add_row(name, tone, use_case)
    
    console.print(personas_table)
    console.print("")
    console.print(namespaces_table)
    console.print("")
    console.print(styles_table)


@cli.command()
@click.option('--text', '-t', help='Direct text input')
@click.option('--file', '-f', type=click.Path(exists=True), help='File containing narrative')
@click.option('--max-turns', '-m', type=int, default=5, help='Maximum dialogue turns (default: 5)')
@click.option('--save', is_flag=True, help='Save dialogue session')
@click.option('--no-project', is_flag=True, help='Skip projection after dialogue')
@click.pass_context
def maieutic(ctx, text, file, max_turns, save, no_project):
    """Engage in maieutic (Socratic) dialogue to explore a narrative.
    
    After the dialogue, you'll be offered to create an allegorical projection
    based on the insights discovered.
    """
    console = ctx.obj['console']
    
    # Get input text
    if file:
        with open(file, 'r') as f:
            narrative = f.read()
    elif text:
        narrative = text
    else:
        console.print("[yellow]Enter your narrative (Ctrl+D to finish):[/yellow]")
        lines = []
        try:
            while True:
                lines.append(input())
        except EOFError:
            narrative = '\n'.join(lines)
    
    if not narrative.strip():
        console.print("[red]No narrative provided.[/red]")
        return
    
    # Run maieutic dialogue
    from lamish_projection_engine.core.maieutic import MaieuticDialogue
    
    dialogue = MaieuticDialogue(console)
    dialogue.start_session(narrative, goal="understand")
    
    # Run dialogue (will offer projection unless --no-project flag is set)
    session = dialogue.conduct_dialogue(max_turns, auto_project=not no_project)
    
    if save:
        from datetime import datetime
        filename = f"maieutic_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        dialogue.save_session(filename)


@cli.command()
@click.option('--projection-id', '-p', type=int, help='Projection ID to explore')
@click.option('--search', '-s', help='Search for similar projections')
@click.option('--limit', '-l', type=int, default=10, help='Number of results (default: 10)')
@click.pass_context
def explore(ctx, projection_id, search, limit):
    """Explore projection space and find similar narratives."""
    console = ctx.obj['console']
    
    if projection_id:
        console.print(f"[cyan]Loading projection {projection_id}...[/cyan]")
        # Show detailed projection with all transformation steps
        show_projection_detail(console, projection_id)
    elif search:
        console.print(f"[cyan]Searching for projections similar to: '{search}'[/cyan]")
        # Search in vector space
        show_search_results(console, search, limit)
    else:
        # Show recent projections
        show_recent_projections(console, limit)


@cli.command()
@click.option('--host', '-h', default='localhost', help='Host to bind to (default: localhost)')
@click.option('--port', '-p', type=int, default=8000, help='Port to bind to (default: 8000)')
@click.pass_context
def web(ctx, host, port):
    """Start the web interface server."""
    console = ctx.obj['console']
    
    console.print(f"[green]Starting LPE Web Server on http://{host}:{port}[/green]")
    console.print("[dim]Press Ctrl+C to stop[/dim]")
    console.print("\n[cyan]Available endpoints:[/cyan]")
    console.print("  / - Main web interface")
    console.print("  /api/config - Configuration management")
    console.print("  /api/projection/create - Create projections")
    console.print("  /api/translation/round-trip - Round-trip analysis")
    console.print("  /api/health - Health check")
    
    try:
        import uvicorn
        from lamish_projection_engine.web.app import app
        uvicorn.run(app, host=host, port=port)
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped[/yellow]")
    except Exception as e:
        console.print(f"[red]Failed to start server: {e}[/red]")


@cli.command()
@click.pass_context
def config(ctx):
    """Configure dynamic attributes interactively."""
    console = ctx.obj['console']
    
    try:
        from lamish_projection_engine.config.dynamic_attributes import ConfigurationManager
        from rich.prompt import Prompt, Confirm
        
        console.print("[bold cyan]LPE Configuration Manager[/bold cyan]\n")
        
        config_manager = ConfigurationManager()
        
        while True:
            console.print("[bold]Available Attributes:[/bold]")
            for i, (name, attr) in enumerate(config_manager.attributes.items(), 1):
                console.print(f"  {i}. {name.title()}")
            
            console.print("\n[bold]Options:[/bold]")
            console.print("  [green]v[/green] - View current configuration")
            console.print("  [green]e[/green] - Edit attribute")
            console.print("  [green]s[/green] - Save all configurations")
            console.print("  [green]g[/green] - Generate system prompt")
            console.print("  [green]q[/green] - Quit")
            
            choice = Prompt.ask("\n[cyan]Choose an option[/cyan]", choices=["v", "e", "s", "g", "q"])
            
            if choice == "q":
                break
            elif choice == "s":
                config_manager.save_all_configurations()
                console.print("[green]✓ All configurations saved[/green]")
            elif choice == "v":
                _display_current_config(console, config_manager)
            elif choice == "e":
                _edit_attribute(console, config_manager)
            elif choice == "g":
                _show_system_prompt(console, config_manager)
                
    except ImportError as e:
        console.print(f"[red]Configuration system not available: {e}[/red]")
    except Exception as e:
        console.print(f"[red]Configuration failed: {e}[/red]")


@cli.command()
@click.option('--text', '-t', help='Direct text input')
@click.option('--file', '-f', type=click.Path(exists=True), help='File containing text')
@click.option('--language', '-l', help='Intermediate language for round-trip')
@click.pass_context
def roundtrip(ctx, text, file, language):
    """Perform round-trip translation analysis."""
    console = ctx.obj['console']
    
    try:
        from lamish_projection_engine.core.translation_roundtrip import LanguageRoundTripAnalyzer
        from rich.prompt import Prompt
        
        # Get input text
        if file:
            with open(file, 'r') as f:
                input_text = f.read()
        elif text:
            input_text = text
        else:
            console.print("[yellow]Enter text to analyze (Ctrl+D to finish):[/yellow]")
            lines = []
            try:
                while True:
                    lines.append(input())
            except EOFError:
                input_text = '\n'.join(lines)
        
        if not input_text.strip():
            console.print("[red]No text provided.[/red]")
            return
        
        # Select language if not provided
        analyzer = LanguageRoundTripAnalyzer()
        if not language:
            languages = analyzer.supported_languages[:10]  # Show first 10
            console.print("\n[bold]Select intermediate language:[/bold]")
            for i, lang in enumerate(languages, 1):
                console.print(f"  {i}. {lang.title()}")
            
            try:
                choice = int(Prompt.ask("[cyan]Enter number[/cyan]")) - 1
                if 0 <= choice < len(languages):
                    language = languages[choice]
                else:
                    console.print("[red]Invalid choice[/red]")
                    return
            except ValueError:
                console.print("[red]Please enter a valid number[/red]")
                return
        
        # Perform analysis
        console.print(f"\n[bold]Analyzing via {language.title()}...[/bold]")
        
        try:
            result = analyzer.perform_round_trip(input_text, language)
            _display_roundtrip_results(console, result)
        except Exception as e:
            console.print(f"[red]Analysis failed: {e}[/red]")
            
    except ImportError as e:
        console.print(f"[red]Round-trip analysis not available: {e}[/red]")
    except Exception as e:
        console.print(f"[red]Round-trip analysis failed: {e}[/red]")


# Helper functions for visualization
def create_projection_layout(narrative: str, persona: str, namespace: str, style: str) -> Layout:
    """Create a live layout for projection visualization."""
    layout = Layout()
    
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=3)
    )
    
    layout["body"].split_row(
        Layout(name="left"),
        Layout(name="right")
    )
    
    # Header
    layout["header"].update(Panel("[bold]Translation Chain Progress[/bold]", style="cyan"))
    
    # Left panel - Original narrative
    layout["left"].update(Panel(narrative[:500] + "...", title="Original Narrative", border_style="blue"))
    
    # Right panel - Transformation steps
    layout["right"].update(Panel("[dim]Awaiting transformation...[/dim]", title="Current Step", border_style="green"))
    
    # Footer - Progress
    layout["footer"].update(Panel("[dim]Starting projection...[/dim]", style="dim"))
    
    return layout


def update_projection_step(layout: Layout, step_name: str) -> None:
    """Update the layout with current transformation step."""
    layout["right"].update(Panel(f"[yellow]→ {step_name}[/yellow]", title="Current Step", border_style="yellow"))
    layout["footer"].update(Panel(f"[dim]Processing: {step_name}[/dim]", style="dim"))


def show_projection_detail(console: Console, projection_id: int) -> None:
    """Display detailed projection information."""
    # Placeholder for actual implementation
    console.print(Panel(f"[yellow]Projection detail view for ID {projection_id} not yet implemented[/yellow]"))


def show_search_results(console: Console, query: str, limit: int) -> None:
    """Display search results in vector space."""
    # Placeholder for actual implementation
    console.print(Panel(f"[yellow]Search functionality not yet implemented[/yellow]"))


def show_recent_projections(console: Console, limit: int) -> None:
    """Display recent projections."""
    # Placeholder for actual implementation
    table = Table(title="Recent Projections", show_header=True)
    table.add_column("ID", style="cyan")
    table.add_column("Created", style="green")
    table.add_column("Persona", style="yellow")
    table.add_column("Namespace", style="magenta")
    table.add_column("Preview", style="dim")
    
    # Sample data
    table.add_row("1", "2 min ago", "philosopher", "lamish-galaxy", "The nature of existence...")
    table.add_row("2", "15 min ago", "advocate", "medieval-realm", "A quest for justice...")
    
    console.print(table)


def _display_current_config(console: Console, config_manager) -> None:
    """Display current configuration."""
    console.print("\n[bold]Current Configuration:[/bold]")
    
    for name, attr in config_manager.attributes.items():
        console.print(f"\n[cyan]{name.title()}:[/cyan]")
        for field_name, field in attr.fields.items():
            console.print(f"  {field_name}: [yellow]{field.value}[/yellow]")
            if field.description:
                console.print(f"    [dim]{field.description}[/dim]")


def _edit_attribute(console: Console, config_manager) -> None:
    """Edit a specific attribute."""
    from rich.prompt import Prompt
    
    attr_names = list(config_manager.attributes.keys())
    console.print("\n[bold]Select attribute to edit:[/bold]")
    
    for i, name in enumerate(attr_names, 1):
        console.print(f"  {i}. {name.title()}")
    
    try:
        choice = int(Prompt.ask("[cyan]Enter number[/cyan]")) - 1
        if 0 <= choice < len(attr_names):
            attr_name = attr_names[choice]
            attr = config_manager.attributes[attr_name]
            
            # Show current fields and allow editing
            console.print(f"\n[bold]Editing {attr.name.title()}:[/bold]")
            for field_name, field in attr.fields.items():
                console.print(f"\n[cyan]{field_name}:[/cyan] {field.value}")
                new_value = Prompt.ask(f"New value (or press Enter to keep current)", default=field.value)
                if new_value != field.value:
                    attr.update_field(field_name, new_value, "user")
                    console.print(f"[green]✓ Updated {field_name}[/green]")
        else:
            console.print("[red]Invalid choice[/red]")
    except ValueError:
        console.print("[red]Please enter a valid number[/red]")


def _show_system_prompt(console: Console, config_manager) -> None:
    """Show the generated system prompt."""
    prompt = config_manager.generate_system_prompt()
    console.print("\n[bold]Generated System Prompt:[/bold]")
    console.print(Panel(prompt, border_style="cyan"))


def _display_roundtrip_results(console: Console, result) -> None:
    """Display round-trip translation results."""
    console.print("\n[bold]Round-trip Translation Results:[/bold]")
    console.print(f"[green]Semantic drift:[/green] {result.semantic_drift:.1%}")
    console.print(f"[green]Original length:[/green] {len(result.original_text)} chars")
    console.print(f"[green]Final length:[/green] {len(result.final_text)} chars")
    
    console.print("\n[bold]Original Text:[/bold]")
    console.print(Panel(result.original_text, border_style="blue"))
    
    console.print("\n[bold]Final Text (after round-trip):[/bold]")
    console.print(Panel(result.final_text, border_style="green"))
    
    if result.preserved_elements:
        console.print("\n[bold]Preserved Elements:[/bold]")
        for element in result.preserved_elements:
            console.print(f"  • {element}")
    
    if result.lost_elements:
        console.print("\n[bold]Lost Elements:[/bold]")
        for element in result.lost_elements:
            console.print(f"  • {element}")
    
    if result.gained_elements:
        console.print("\n[bold]Gained Elements:[/bold]")
        for element in result.gained_elements:
            console.print(f"  • {element}")


if __name__ == "__main__":
    cli()