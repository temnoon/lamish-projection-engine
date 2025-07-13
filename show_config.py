#!/usr/bin/env python3
"""Show current LPE configuration."""
import os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

def show_config():
    """Display current configuration."""
    console.print(Panel.fit(
        "[bold]LPE Configuration[/bold]\n"
        "Current settings from environment and .env file",
        border_style="cyan"
    ))
    
    # Check if .env exists
    if os.path.exists('.env'):
        console.print("\n[green]✓ .env file found[/green]")
    else:
        console.print("\n[yellow]⚠ No .env file found, using defaults[/yellow]")
        console.print("  Create one with: cp .env.example .env")
    
    # Load and display config
    try:
        from lamish_projection_engine.utils.config import get_config, reload_config
        
        # Force reload to get latest values
        config = reload_config()
        
        # Create config table
        table = Table(title="Current Settings", show_header=True)
        table.add_column("Setting", style="cyan", width=30)
        table.add_column("Value", style="green")
        table.add_column("Source", style="dim")
        
        # Database settings
        table.add_section()
        table.add_row("Database", "", "")
        table.add_row("  Host", config.postgres_host, "env/default")
        table.add_row("  Port", str(config.postgres_port), "env/default")
        table.add_row("  Database", config.postgres_db, "env/default")
        table.add_row("  User", config.postgres_user, "env/default")
        
        # LLM settings
        table.add_section()
        table.add_row("LLM Configuration", "", "")
        table.add_row("  Ollama Host", config.ollama_host, "env/default")
        table.add_row("  LLM Model", config.llm_model, "env/default")
        table.add_row("  Embedding Model", config.embedding_model, "env/default")
        table.add_row("  Temperature", str(config.llm_temperature), "env/default")
        table.add_row("  Max Tokens", str(config.llm_max_tokens), "env/default")
        table.add_row("  Use Mock LLM", str(config.use_mock_llm), "env/default")
        
        # App settings
        table.add_section()
        table.add_row("Application", "", "")
        table.add_row("  Debug", str(config.debug), "env/default")
        table.add_row("  Log Level", config.log_level, "env/default")
        
        console.print(table)
        
        # Show environment variables
        console.print("\n[cyan]Environment Variables:[/cyan]")
        env_vars = {k: v for k, v in os.environ.items() if k.startswith('LPE_')}
        if env_vars:
            for key, value in sorted(env_vars.items()):
                console.print(f"  {key}={value}")
        else:
            console.print("  [dim]No LPE_ environment variables set[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error loading configuration: {e}[/red]")
        import traceback
        traceback.print_exc()


def main():
    """Main entry point."""
    show_config()
    
    console.print("\n[dim]To change settings:[/dim]")
    console.print("[dim]1. Edit .env file[/dim]")
    console.print("[dim]2. Set environment variables: export LPE_LLM_MODEL=gemma3:12b[/dim]")
    console.print("[dim]3. Restart the application to pick up changes[/dim]")


if __name__ == "__main__":
    main()