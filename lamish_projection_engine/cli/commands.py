"""CLI command implementations for LPE."""
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich.layout import Layout
import time
from typing import Optional
import json
import sys

from lamish_projection_engine.core.projection import ProjectionEngine, TranslationChain
from lamish_projection_engine.core.database import get_db_manager
from lamish_projection_engine.core.models import (
    Base, Persona, Namespace, LanguageStyle, AgentConfiguration,
    SourceNarrative, Projection as ProjectionModel, TranslationChainStep,
    seed_initial_data
)


class ProjectionCLI:
    """Handles CLI operations for projections."""
    
    def __init__(self, console: Console):
        self.console = console
        self.engine = ProjectionEngine(console)
        self.db_manager = get_db_manager()
    
    def initialize_database(self):
        """Initialize database and seed initial data."""
        try:
            # Create tables
            Base.metadata.create_all(bind=self.db_manager.engine)
            
            # Seed initial data
            with self.db_manager.get_session() as session:
                seed_initial_data(session)
            
            self.console.print("[green]✓ Database initialized successfully[/green]")
        except Exception as e:
            self.console.print(f"[red]Failed to initialize database: {e}[/red]")
            raise
    
    def project_narrative(self, narrative: str, persona: str, namespace: str, 
                         style: str, interactive: bool, show_steps: bool):
        """Project a narrative using the translation chain."""
        try:
            # Verify configuration exists
            with self.db_manager.get_session() as session:
                persona_obj = session.query(Persona).filter_by(name=persona).first()
                namespace_obj = session.query(Namespace).filter_by(name=namespace).first()
                style_obj = session.query(LanguageStyle).filter_by(name=style).first()
                
                if not all([persona_obj, namespace_obj, style_obj]):
                    missing = []
                    if not persona_obj: missing.append(f"persona '{persona}'")
                    if not namespace_obj: missing.append(f"namespace '{namespace}'")
                    if not style_obj: missing.append(f"style '{style}'")
                    self.console.print(f"[red]Error: Missing {', '.join(missing)}[/red]")
                    return None
            
            # Create projection
            if interactive:
                self.console.print("[yellow]Interactive mode not yet implemented[/yellow]")
                return None
            
            projection = self.engine.create_projection(
                narrative, persona, namespace, style, show_steps
            )
            
            # Save to database
            self._save_projection_to_db(projection)
            
            return projection
            
        except Exception as e:
            self.console.print(f"[red]Projection failed: {e}[/red]")
            return None
    
    def _save_projection_to_db(self, projection):
        """Save projection to database."""
        try:
            with self.db_manager.get_session() as session:
                # Get or create source narrative
                source = session.query(SourceNarrative).filter_by(
                    content=projection.source_narrative
                ).first()
                
                if not source:
                    source = SourceNarrative(content=projection.source_narrative)
                    session.add(source)
                    session.flush()
                
                # Get agent configuration
                persona = session.query(Persona).filter_by(name=projection.persona).first()
                namespace = session.query(Namespace).filter_by(name=projection.namespace).first()
                style = session.query(LanguageStyle).filter_by(name=projection.style).first()
                
                agent_config = session.query(AgentConfiguration).filter_by(
                    persona_id=persona.id,
                    namespace_id=namespace.id,
                    language_style_id=style.id
                ).first()
                
                if not agent_config:
                    agent_config = AgentConfiguration(
                        name=f"{persona.name}-{namespace.name}-{style.name}",
                        persona_id=persona.id,
                        namespace_id=namespace.id,
                        language_style_id=style.id
                    )
                    session.add(agent_config)
                    session.flush()
                
                # Create projection record
                db_projection = ProjectionModel(
                    source_narrative_id=source.id,
                    agent_configuration_id=agent_config.id,
                    content=projection.final_projection,
                    reflection=projection.reflection
                )
                session.add(db_projection)
                session.flush()
                
                # Save translation steps
                for i, step in enumerate(projection.steps):
                    db_step = TranslationChainStep(
                        projection_id=db_projection.id,
                        step_name=step.name,
                        step_order=i,
                        input_data={"text": step.input_snapshot},
                        output_data={"text": step.output_snapshot},
                        meta_data=step.metadata,
                        duration_ms=step.duration_ms
                    )
                    session.add(db_step)
                
                session.commit()
                self.console.print(f"[green]✓ Projection saved to database (ID: {db_projection.id})[/green]")
                
        except Exception as e:
            self.console.print(f"[red]Failed to save projection: {e}[/red]")
    
    def list_recent_projections(self, limit: int = 10):
        """List recent projections from database."""
        try:
            with self.db_manager.get_session() as session:
                projections = session.query(ProjectionModel)\
                    .order_by(ProjectionModel.created_at.desc())\
                    .limit(limit)\
                    .all()
                
                if not projections:
                    self.console.print("[yellow]No projections found[/yellow]")
                    return
                
                table = Table(title="Recent Projections", show_header=True)
                table.add_column("ID", style="cyan", width=6)
                table.add_column("Created", style="green", width=15)
                table.add_column("Persona", style="yellow", width=12)
                table.add_column("Namespace", style="magenta", width=15)
                table.add_column("Style", style="blue", width=10)
                table.add_column("Preview", style="dim", width=40)
                
                for proj in projections:
                    config = proj.agent_configuration
                    preview = proj.content[:60] + "..." if len(proj.content) > 60 else proj.content
                    
                    table.add_row(
                        str(proj.id),
                        proj.created_at.strftime("%Y-%m-%d %H:%M"),
                        config.persona.name,
                        config.namespace.name,
                        config.language_style.name,
                        preview
                    )
                
                self.console.print(table)
                
        except Exception as e:
            self.console.print(f"[red]Failed to list projections: {e}[/red]")
    
    def show_projection_detail(self, projection_id: int):
        """Show detailed information about a projection."""
        try:
            with self.db_manager.get_session() as session:
                projection = session.query(ProjectionModel)\
                    .filter_by(id=projection_id)\
                    .first()
                
                if not projection:
                    self.console.print(f"[red]Projection {projection_id} not found[/red]")
                    return
                
                # Create detail tree
                tree = Tree(f"[bold]Projection #{projection_id}[/bold]")
                
                # Metadata
                meta = tree.add("[cyan]Metadata[/cyan]")
                meta.add(f"Created: {projection.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                meta.add(f"UUID: {projection.uuid}")
                
                # Configuration
                config = projection.agent_configuration
                config_node = tree.add("[cyan]Configuration[/cyan]")
                config_node.add(f"Persona: [yellow]{config.persona.name}[/yellow]")
                config_node.add(f"Namespace: [magenta]{config.namespace.name}[/magenta]")
                config_node.add(f"Style: [blue]{config.language_style.name}[/blue]")
                
                # Translation steps
                steps_node = tree.add("[cyan]Translation Chain[/cyan]")
                for step in projection.translation_steps:
                    step_detail = steps_node.add(
                        f"{step.step_name} [dim]({step.duration_ms}ms)[/dim]"
                    )
                    output_text = step.output_data.get('text', '')
                    preview = output_text[:80] + "..." if len(output_text) > 80 else output_text
                    step_detail.add(f"[dim]{preview}[/dim]")
                
                self.console.print(Panel(tree, border_style="green"))
                
                # Source narrative
                self.console.print(Panel(
                    projection.source_narrative.content,
                    title="[bold]Source Narrative[/bold]",
                    border_style="blue"
                ))
                
                # Final projection
                self.console.print(Panel(
                    projection.content,
                    title="[bold]Final Projection[/bold]",
                    border_style="cyan"
                ))
                
                # Reflection
                if projection.reflection:
                    self.console.print(Panel(
                        projection.reflection,
                        title="[bold]Reflection[/bold]",
                        border_style="magenta"
                    ))
                
        except Exception as e:
            self.console.print(f"[red]Failed to show projection detail: {e}[/red]")
    
    def search_projections(self, query: str, limit: int = 10):
        """Search for projections containing query text."""
        try:
            with self.db_manager.get_session() as session:
                # Simple text search - in production would use vector similarity
                projections = session.query(ProjectionModel)\
                    .filter(
                        ProjectionModel.content.ilike(f"%{query}%") |
                        ProjectionModel.reflection.ilike(f"%{query}%")
                    )\
                    .limit(limit)\
                    .all()
                
                if not projections:
                    self.console.print(f"[yellow]No projections found matching '{query}'[/yellow]")
                    return
                
                self.console.print(f"[cyan]Found {len(projections)} projections matching '{query}':[/cyan]")
                
                for proj in projections:
                    config = proj.agent_configuration
                    self.console.print(
                        f"\n[bold]#{proj.id}[/bold] - "
                        f"{config.persona.name}/{config.namespace.name} - "
                        f"[dim]{proj.created_at.strftime('%Y-%m-%d')}[/dim]"
                    )
                    
                    # Highlight matching text
                    content_preview = proj.content[:200] + "..." if len(proj.content) > 200 else proj.content
                    highlighted = content_preview.replace(
                        query, f"[bold yellow]{query}[/bold yellow]"
                    )
                    self.console.print(f"  {highlighted}")
                
        except Exception as e:
            self.console.print(f"[red]Search failed: {e}[/red]")