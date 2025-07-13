#!/usr/bin/env python3
"""Test LLM functionality for LPE."""
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

def test_llm():
    """Test LLM connection and functionality."""
    console.print(Panel.fit(
        "[bold]LPE LLM Test[/bold]\n"
        "Testing Ollama connection and models",
        border_style="cyan"
    ))
    
    # Test basic connection
    console.print("\n[cyan]1. Testing LLM connection...[/cyan]")
    try:
        from lamish_projection_engine.core.llm import get_llm_provider, test_llm_connection
        test_llm_connection()
    except Exception as e:
        console.print(f"[red]Connection test failed: {e}[/red]")
        return False
    
    # Test projection
    console.print("\n[cyan]2. Testing narrative projection...[/cyan]")
    try:
        from lamish_projection_engine.core.projection import TranslationChain
        
        sample_narrative = """
        The startup founder realized their innovative app was being copied by a tech giant. 
        Years of hard work seemed threatened as the larger company's resources dwarfed their own.
        """
        
        chain = TranslationChain(
            persona="philosopher",
            namespace="lamish-galaxy", 
            style="poetic",
            console=console,
            verbose=True
        )
        
        projection = chain.run(sample_narrative, show_steps=True)
        
        console.print("\n[green]✓ Projection completed successfully![/green]")
        
        # Show embedding info
        if projection.embedding:
            console.print(f"\n[cyan]Embedding generated:[/cyan] {len(projection.embedding)} dimensions")
        else:
            console.print("\n[yellow]No embedding generated[/yellow]")
            
        return True
        
    except Exception as e:
        console.print(f"[red]Projection test failed: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False


def check_models():
    """Check available models."""
    console.print("\n[cyan]3. Checking available models...[/cyan]")
    
    try:
        from lamish_projection_engine.core.llm import get_llm_provider
        provider = get_llm_provider()
        
        table = Table(title="LLM Configuration", show_header=True)
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Provider", provider.__class__.__name__)
        table.add_row("Available", str(provider.is_available()))
        
        if hasattr(provider, 'model'):
            table.add_row("Text Model", provider.model)
        if hasattr(provider, 'embedding_model'):
            table.add_row("Embedding Model", provider.embedding_model)
        
        if hasattr(provider, 'list_models'):
            models = provider.list_models()
            table.add_row("Available Models", ", ".join(models[:3]) + "..." if len(models) > 3 else ", ".join(models))
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error checking models: {e}[/red]")


def main():
    """Run all LLM tests."""
    console.print("[bold]Starting LLM tests...[/bold]\n")
    
    # Check models first
    check_models()
    
    # Run functional test
    success = test_llm()
    
    if success:
        console.print("\n[bold green]✓ All LLM tests passed![/bold green]")
        console.print("\nYour LLM integration is working correctly.")
    else:
        console.print("\n[bold red]✗ Some tests failed[/bold red]")
        console.print("\nTroubleshooting:")
        console.print("1. Make sure Ollama is running: ollama serve")
        console.print("2. Check available models: ollama list")
        console.print("3. Pull required models: ./setup_ollama.sh")
        console.print("4. Set USE_MOCK_LLM=true in .env to use mock LLM")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())