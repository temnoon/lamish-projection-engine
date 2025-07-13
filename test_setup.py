#!/usr/bin/env python3
"""Test script to verify LPE setup."""
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def test_imports():
    """Test that all required imports work."""
    console.print("[cyan]Testing imports...[/cyan]")
    
    modules = []
    
    # Core imports
    try:
        import sqlalchemy
        modules.append(("SQLAlchemy", "✓", sqlalchemy.__version__))
    except ImportError as e:
        modules.append(("SQLAlchemy", "✗", str(e)))
    
    try:
        import psycopg2
        modules.append(("psycopg2", "✓", psycopg2.__version__))
    except ImportError as e:
        modules.append(("psycopg2", "✗", str(e)))
    
    try:
        import pgvector
        modules.append(("pgvector", "✓", "Installed"))
    except ImportError as e:
        modules.append(("pgvector", "✗", str(e)))
    
    try:
        import click
        modules.append(("Click", "✓", click.__version__))
    except ImportError as e:
        modules.append(("Click", "✗", str(e)))
    
    try:
        import rich
        # Rich doesn't have __version__ directly
        from importlib.metadata import version
        try:
            rich_version = version('rich')
        except:
            rich_version = "Unknown"
        modules.append(("Rich", "✓", rich_version))
    except ImportError as e:
        modules.append(("Rich", "✗", str(e)))
    
    try:
        import pydantic
        modules.append(("Pydantic", "✓", pydantic.__version__))
    except ImportError as e:
        modules.append(("Pydantic", "✗", str(e)))
    
    # Display results
    table = Table(title="Import Test Results", show_header=True)
    table.add_column("Module", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Version/Error")
    
    all_ok = True
    for module, status, info in modules:
        if status == "✗":
            all_ok = False
            table.add_row(module, f"[red]{status}[/red]", f"[red]{info}[/red]")
        else:
            table.add_row(module, f"[green]{status}[/green]", info)
    
    console.print(table)
    return all_ok


def test_lpe_imports():
    """Test LPE-specific imports."""
    console.print("\n[cyan]Testing LPE imports...[/cyan]")
    
    lpe_modules = []
    
    try:
        from lamish_projection_engine.core.projection import ProjectionEngine
        lpe_modules.append(("ProjectionEngine", "✓"))
    except ImportError as e:
        lpe_modules.append(("ProjectionEngine", f"✗ {e}"))
    
    try:
        from lamish_projection_engine.core.database import get_db_manager
        lpe_modules.append(("Database Manager", "✓"))
    except ImportError as e:
        lpe_modules.append(("Database Manager", f"✗ {e}"))
    
    try:
        from lamish_projection_engine.cli.main import cli
        lpe_modules.append(("CLI", "✓"))
    except ImportError as e:
        lpe_modules.append(("CLI", f"✗ {e}"))
    
    all_ok = True
    for module, status in lpe_modules:
        if status.startswith("✗"):
            all_ok = False
            console.print(f"  {module}: [red]{status}[/red]")
        else:
            console.print(f"  {module}: [green]{status}[/green]")
    
    return all_ok


def test_database():
    """Test database connection."""
    console.print("\n[cyan]Testing database connection...[/cyan]")
    
    try:
        from lamish_projection_engine.core.database import check_connection
        if check_connection():
            console.print("  Database: [green]✓ Connected[/green]")
            return True
        else:
            console.print("  Database: [red]✗ Not connected[/red]")
            console.print("  [yellow]Make sure PostgreSQL is running: docker-compose up -d[/yellow]")
            return False
    except Exception as e:
        console.print(f"  Database: [red]✗ Error: {e}[/red]")
        return False


def main():
    """Run all tests."""
    console.print(Panel.fit(
        "[bold]LPE Setup Test[/bold]\n"
        "Checking your installation...",
        border_style="cyan"
    ))
    
    # Check Python version
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 8):
        console.print(f"\nPython version: [green]✓ {py_version}[/green]")
    else:
        console.print(f"\nPython version: [red]✗ {py_version} (Need 3.8+)[/red]")
        return 1
    
    # Run tests
    imports_ok = test_imports()
    lpe_ok = test_lpe_imports()
    db_ok = test_database()
    
    # Summary
    console.print("\n" + "="*50)
    if imports_ok and lpe_ok and db_ok:
        console.print("[bold green]✓ All tests passed![/bold green]")
        console.print("\nYou're ready to use LPE! Try:")
        console.print("  python demo.py")
        return 0
    else:
        console.print("[bold red]✗ Some tests failed[/bold red]")
        console.print("\nPlease check the errors above and:")
        console.print("1. Make sure you're in the virtual environment")
        console.print("2. Run: pip install -r requirements.txt")
        console.print("3. Ensure PostgreSQL is running: docker-compose up -d")
        return 1


if __name__ == "__main__":
    sys.exit(main())