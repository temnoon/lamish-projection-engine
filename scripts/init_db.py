#!/usr/bin/env python3
"""Initialize the LPE database with tables and seed data."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lamish_projection_engine.core.database import get_db_manager
from lamish_projection_engine.core.models import Base, seed_initial_data
from rich.console import Console

console = Console()


def main():
    """Initialize database."""
    console.print("[cyan]Initializing Lamish Projection Engine database...[/cyan]")
    
    try:
        # Get database manager
        db_manager = get_db_manager()
        
        # Check connection
        if not db_manager.check_connection():
            console.print("[red]Error: Cannot connect to database[/red]")
            console.print("Make sure PostgreSQL is running: docker-compose up -d")
            return 1
        
        # Create pgvector extension
        with db_manager.engine.connect() as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            conn.commit()
        
        # Create tables
        Base.metadata.create_all(bind=db_manager.engine)
        console.print("[green]✓ Database tables created[/green]")
        
        # Seed initial data
        with db_manager.get_session() as session:
            seed_initial_data(session)
        
        console.print("[green]✓ Initial data seeded[/green]")
        console.print("[bold green]Database initialization complete![/bold green]")
        
        return 0
        
    except Exception as e:
        console.print(f"[red]Error during initialization: {e}[/red]")
        return 1


if __name__ == "__main__":
    sys.exit(main())