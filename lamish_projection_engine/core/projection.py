"""Core projection engine for narrative transformation."""
import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Protocol
from abc import ABC, abstractmethod
import hashlib
import logging
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree
from rich.progress import Progress, SpinnerColumn, TextColumn

from lamish_projection_engine.core.llm import LLMTransformer, get_llm_provider

logger = logging.getLogger(__name__)


@dataclass
class ProjectionStep:
    """Represents a single step in the transformation chain."""
    name: str
    input_snapshot: str
    output_snapshot: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: int = 0


@dataclass
class Projection:
    """Complete projection with all transformation steps."""
    id: Optional[int]
    source_narrative: str
    final_projection: str
    reflection: str
    persona: str
    namespace: str
    style: str
    steps: List[ProjectionStep] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    embedding: Optional[List[float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert projection to dictionary for storage."""
        return {
            'id': self.id,
            'source_narrative': self.source_narrative,
            'final_projection': self.final_projection,
            'reflection': self.reflection,
            'persona': self.persona,
            'namespace': self.namespace,
            'style': self.style,
            'steps': [
                {
                    'name': step.name,
                    'input_snapshot': step.input_snapshot,
                    'output_snapshot': step.output_snapshot,
                    'metadata': step.metadata,
                    'timestamp': step.timestamp.isoformat(),
                    'duration_ms': step.duration_ms
                }
                for step in self.steps
            ],
            'created_at': self.created_at.isoformat(),
            'embedding': self.embedding
        }


class TransformationStrategy(Protocol):
    """Protocol for transformation strategies."""
    def transform(self, input_text: str, context: Dict[str, Any]) -> str:
        """Transform input text with given context."""
        ...




class TranslationChain:
    """Orchestrates the complete translation chain process."""
    
    def __init__(self, persona: str, namespace: str, style: str, 
                 console: Optional[Console] = None, verbose: bool = True):
        self.persona = persona
        self.namespace = namespace
        self.style = style
        self.console = console or Console()
        self.verbose = verbose
        # Use the proper LLMTransformer from llm module
        self.transformer = LLMTransformer(persona, namespace, style)
    
    def run(self, source_narrative: str, show_steps: bool = True) -> Projection:
        """Execute the complete translation chain."""
        projection = Projection(
            id=None,
            source_narrative=source_narrative,
            final_projection="",
            reflection="",
            persona=self.persona,
            namespace=self.namespace,
            style=self.style
        )
        
        # Define transformation pipeline
        pipeline = [
            ("Deconstructing narrative", "deconstruct"),
            ("Mapping to namespace", "map"),
            ("Reconstructing allegory", "reconstruct"),
            ("Applying style", "stylize"),
            ("Generating reflection", "reflect")
        ]
        
        current_text = source_narrative
        
        if show_steps and self.verbose:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
                transient=True
            ) as progress:
                
                for step_name, step_type in pipeline:
                    task = progress.add_task(f"[cyan]{step_name}...[/cyan]")
                    
                    start_time = time.time()
                    output_text = self.transformer.transform(current_text, step_type)
                    duration_ms = int((time.time() - start_time) * 1000)
                    
                    # Record step
                    step = ProjectionStep(
                        name=step_name,
                        input_snapshot=current_text[:200] + "..." if len(current_text) > 200 else current_text,
                        output_snapshot=output_text[:200] + "..." if len(output_text) > 200 else output_text,
                        metadata={"step_type": step_type},
                        duration_ms=duration_ms
                    )
                    projection.steps.append(step)
                    
                    # Update for next iteration
                    if step_type != "reflect":
                        current_text = output_text
                    
                    progress.update(task, completed=True)
                    time.sleep(0.5)  # Simulate processing time
        
        else:
            # Run without visual feedback
            for step_name, step_type in pipeline:
                start_time = time.time()
                output_text = self.transformer.transform(current_text, step_type)
                duration_ms = int((time.time() - start_time) * 1000)
                
                step = ProjectionStep(
                    name=step_name,
                    input_snapshot=current_text[:200] + "..." if len(current_text) > 200 else current_text,
                    output_snapshot=output_text[:200] + "..." if len(output_text) > 200 else output_text,
                    metadata={"step_type": step_type},
                    duration_ms=duration_ms
                )
                projection.steps.append(step)
                
                if step_type != "reflect":
                    current_text = output_text
        
        # Set final outputs
        projection.final_projection = current_text
        projection.reflection = projection.steps[-1].output_snapshot
        
        # Generate embedding for the final projection
        try:
            projection.embedding = self.transformer.generate_embedding(projection.final_projection)
            logger.info(f"Generated embedding with {len(projection.embedding)} dimensions")
        except Exception as e:
            logger.warning(f"Could not generate embedding: {e}")
            projection.embedding = None
        
        if self.verbose:
            self._display_results(projection)
        
        return projection
    
    def _display_results(self, projection: Projection):
        """Display the projection results in a formatted way."""
        # Create result tree
        tree = Tree("[bold]Projection Complete[/bold]")
        
        # Add configuration
        config = tree.add("[cyan]Configuration[/cyan]")
        config.add(f"Persona: [yellow]{projection.persona}[/yellow]")
        config.add(f"Namespace: [yellow]{projection.namespace}[/yellow]")
        config.add(f"Style: [yellow]{projection.style}[/yellow]")
        
        # Add transformation chain
        chain = tree.add("[cyan]Translation Chain[/cyan]")
        total_duration = sum(step.duration_ms for step in projection.steps)
        for step in projection.steps:
            step_node = chain.add(f"{step.name} [dim]({step.duration_ms}ms)[/dim]")
            step_node.add(f"[dim]Output: {step.output_snapshot[:60]}...[/dim]")
        
        chain.add(f"[bold]Total duration: {total_duration}ms[/bold]")
        
        self.console.print(Panel(tree, border_style="green"))
        
        # Display final projection
        self.console.print(Panel(
            projection.final_projection,
            title="[bold]Final Projection[/bold]",
            border_style="cyan"
        ))
        
        # Display reflection
        self.console.print(Panel(
            projection.reflection,
            title="[bold]Reflection[/bold]",
            border_style="magenta"
        ))


class ProjectionEngine:
    """Main engine for managing projections."""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.projections: List[Projection] = []
    
    def create_projection(self, narrative: str, persona: str, namespace: str, 
                         style: str, show_steps: bool = True) -> Projection:
        """Create a new projection."""
        chain = TranslationChain(persona, namespace, style, self.console)
        projection = chain.run(narrative, show_steps)
        projection.id = len(self.projections) + 1
        self.projections.append(projection)
        return projection
    
    def get_projection(self, projection_id: int) -> Optional[Projection]:
        """Retrieve a projection by ID."""
        for proj in self.projections:
            if proj.id == projection_id:
                return proj
        return None
    
    def search_projections(self, query: str, limit: int = 10) -> List[Projection]:
        """Search projections (mock implementation)."""
        # In real implementation, this would use vector similarity
        results = []
        query_lower = query.lower()
        
        for proj in self.projections:
            if (query_lower in proj.source_narrative.lower() or
                query_lower in proj.final_projection.lower() or
                query_lower in proj.reflection.lower()):
                results.append(proj)
                if len(results) >= limit:
                    break
        
        return results