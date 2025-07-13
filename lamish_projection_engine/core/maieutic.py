"""Maieutic (Socratic) dialogue system for narrative exploration."""
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown
from rich.tree import Tree
from rich.table import Table
import logging

from lamish_projection_engine.core.llm import get_llm_provider, LLMProvider
from lamish_projection_engine.core.projection import TranslationChain, Projection
from lamish_projection_engine.utils.config import get_config

logger = logging.getLogger(__name__)


@dataclass
class DialogueTurn:
    """A single turn in the maieutic dialogue."""
    question: str
    answer: str
    timestamp: datetime = field(default_factory=datetime.now)
    insights: List[str] = field(default_factory=list)
    depth_level: int = 0


@dataclass
class MaieuticSession:
    """A complete maieutic dialogue session."""
    id: Optional[int] = None
    initial_narrative: str = ""
    goal: str = ""
    turns: List[DialogueTurn] = field(default_factory=list)
    extracted_elements: Dict[str, Any] = field(default_factory=dict)
    final_understanding: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            'id': self.id,
            'initial_narrative': self.initial_narrative,
            'goal': self.goal,
            'turns': [
                {
                    'question': turn.question,
                    'answer': turn.answer,
                    'insights': turn.insights,
                    'depth_level': turn.depth_level,
                    'timestamp': turn.timestamp.isoformat()
                }
                for turn in self.turns
            ],
            'extracted_elements': self.extracted_elements,
            'final_understanding': self.final_understanding,
            'created_at': self.created_at.isoformat()
        }


class MaieuticDialogue:
    """Conducts maieutic (Socratic) dialogues to explore narratives."""
    
    def __init__(self, console: Optional[Console] = None, 
                 provider: Optional[LLMProvider] = None):
        self.console = console or Console()
        self.provider = provider or get_llm_provider()
        self.session = None
        
    def start_session(self, narrative: str, goal: str = "understand") -> MaieuticSession:
        """Start a new maieutic dialogue session."""
        self.session = MaieuticSession(
            initial_narrative=narrative,
            goal=goal
        )
        return self.session
    
    def generate_question(self, depth_level: int = 0) -> str:
        """Generate the next maieutic question based on dialogue history."""
        system_prompt = """You are a Socratic questioner practicing maieutic dialogue.
Your role is to help the user discover deeper truths about their narrative through thoughtful questions.
Do not provide answers or interpretations - only ask questions that guide discovery.
Focus on one aspect at a time, building understanding gradually.
Questions should be open-ended and thought-provoking."""
        
        # Build context from session
        context = f"Initial narrative: {self.session.initial_narrative}\n\n"
        
        if self.session.turns:
            context += "Dialogue so far:\n"
            for turn in self.session.turns[-3:]:  # Last 3 turns for context
                context += f"Q: {turn.question}\n"
                context += f"A: {turn.answer}\n\n"
        
        # Depth-specific prompting
        depth_prompts = {
            0: "Ask an initial question to understand the surface level of the narrative.",
            1: "Ask about the underlying motivations or conflicts.",
            2: "Probe deeper into the root causes or fundamental tensions.",
            3: "Question the assumptions or worldview behind the narrative.",
            4: "Explore the universal or archetypal elements present."
        }
        
        prompt = f"""{context}

Depth level: {depth_level}
Instruction: {depth_prompts.get(depth_level, depth_prompts[2])}

Generate a single, thoughtful question to continue the maieutic dialogue:"""
        
        try:
            question = self.provider.generate(prompt, system_prompt)
            return question.strip()
        except Exception as e:
            logger.error(f"Error generating question: {e}")
            # Fallback questions
            fallbacks = [
                "What do you think is the core conflict in this narrative?",
                "Why do you think this situation arose?",
                "What assumptions might be underlying this story?",
                "What would happen if we looked at this from another perspective?",
                "What deeper pattern might this represent?"
            ]
            return fallbacks[depth_level % len(fallbacks)]
    
    def extract_insights(self, question: str, answer: str) -> List[str]:
        """Extract key insights from an answer."""
        system_prompt = """You are analyzing a maieutic dialogue to extract key insights.
Identify 1-3 brief, specific insights revealed by the answer.
Focus on what was discovered or clarified, not just what was said."""
        
        prompt = f"""Question: {question}
Answer: {answer}

List 1-3 key insights revealed by this answer (one per line):"""
        
        try:
            response = self.provider.generate(prompt, system_prompt)
            insights = [line.strip() for line in response.strip().split('\n') 
                       if line.strip() and not line.strip().startswith('#')]
            return insights[:3]  # Max 3 insights
        except:
            return ["New perspective revealed"]
    
    def synthesize_understanding(self) -> str:
        """Synthesize the final understanding from the dialogue."""
        if not self.session or not self.session.turns:
            return "No dialogue conducted yet."
        
        system_prompt = """You are synthesizing the discoveries from a maieutic dialogue.
Summarize what was collectively discovered through the questioning process.
Focus on insights that emerged, not just a retelling of the conversation."""
        
        dialogue_text = "Maieutic Dialogue Summary:\n\n"
        dialogue_text += f"Original narrative: {self.session.initial_narrative}\n\n"
        
        for i, turn in enumerate(self.session.turns):
            dialogue_text += f"Q{i+1}: {turn.question}\n"
            dialogue_text += f"A{i+1}: {turn.answer}\n"
            if turn.insights:
                dialogue_text += f"Insights: {', '.join(turn.insights)}\n"
            dialogue_text += "\n"
        
        prompt = f"""{dialogue_text}

Based on this maieutic dialogue, synthesize the key understanding that emerged:"""
        
        try:
            return self.provider.generate(prompt, system_prompt)
        except:
            return "Through questioning, deeper layers of meaning were revealed."
    
    def conduct_dialogue(self, max_turns: int = 5, auto_project: bool = True) -> MaieuticSession:
        """Conduct an interactive maieutic dialogue.
        
        Args:
            max_turns: Maximum number of question-answer turns
            auto_project: Whether to offer projection after dialogue
        """
        if not self.session:
            raise ValueError("No session started. Call start_session first.")
        
        self.console.print(Panel(
            "[bold cyan]Maieutic Dialogue[/bold cyan]\n"
            "[dim]Through questions, we'll explore the deeper meaning of your narrative.[/dim]",
            border_style="cyan"
        ))
        
        self.console.print(f"\n[bold]Initial narrative:[/bold]")
        self.console.print(Panel(self.session.initial_narrative, border_style="dim"))
        
        for turn_num in range(max_turns):
            self.console.print(f"\n[cyan]--- Turn {turn_num + 1} ---[/cyan]")
            
            # Generate question
            depth = min(turn_num, 4)  # Max depth 4
            question = self.generate_question(depth)
            
            self.console.print(f"\n[bold yellow]Question:[/bold yellow] {question}")
            
            # Get answer
            answer = Prompt.ask("\n[green]Your response[/green]")
            
            if answer.lower() in ['quit', 'exit', 'done']:
                break
            
            # Extract insights
            self.console.print("\n[dim]Extracting insights...[/dim]")
            insights = self.extract_insights(question, answer)
            
            # Record turn
            turn = DialogueTurn(
                question=question,
                answer=answer,
                insights=insights,
                depth_level=depth
            )
            self.session.turns.append(turn)
            
            # Show insights
            if insights:
                self.console.print("\n[bold]Insights discovered:[/bold]")
                for insight in insights:
                    self.console.print(f"  • {insight}")
            
            # Ask if continue
            if turn_num < max_turns - 1:
                if not Confirm.ask("\n[cyan]Continue dialogue?[/cyan]", default=True):
                    break
        
        # Synthesize understanding
        self.console.print("\n[dim]Synthesizing understanding...[/dim]")
        self.session.final_understanding = self.synthesize_understanding()
        
        # Display results
        self._display_results()
        
        # Offer projection based on insights
        if auto_project:
            self._offer_projection()
        
        return self.session
    
    def _display_results(self):
        """Display the dialogue results."""
        tree = Tree("[bold]Maieutic Dialogue Complete[/bold]")
        
        # Add turns
        turns_branch = tree.add("[cyan]Dialogue Flow[/cyan]")
        for i, turn in enumerate(self.session.turns):
            turn_node = turns_branch.add(f"Turn {i+1} (Depth: {turn.depth_level})")
            turn_node.add(f"[yellow]Q:[/yellow] {turn.question[:60]}...")
            turn_node.add(f"[green]A:[/green] {turn.answer[:60]}...")
            if turn.insights:
                insights_node = turn_node.add("[magenta]Insights:[/magenta]")
                for insight in turn.insights:
                    insights_node.add(f"• {insight}")
        
        self.console.print(Panel(tree, border_style="green"))
        
        # Display final understanding
        self.console.print(Panel(
            self.session.final_understanding,
            title="[bold]Emergent Understanding[/bold]",
            border_style="cyan"
        ))
    
    def _offer_projection(self):
        """Offer to create an allegorical projection based on dialogue insights."""
        if not Confirm.ask("\n[cyan]Create an allegorical projection based on these insights?[/cyan]"):
            return
        
        self.console.print("\n[bold]Projection Configuration[/bold]")
        self.console.print("[dim]Based on your dialogue, I'll suggest appropriate settings.[/dim]\n")
        
        # Suggest configuration based on insights
        suggested_persona, suggested_namespace, suggested_style = self._suggest_configuration()
        
        # Display suggestions
        self.console.print(f"Suggested persona: [yellow]{suggested_persona}[/yellow]")
        self.console.print(f"Suggested namespace: [magenta]{suggested_namespace}[/magenta]")
        self.console.print(f"Suggested style: [blue]{suggested_style}[/blue]")
        
        # Allow customization
        if Confirm.ask("\n[cyan]Customize these settings?[/cyan]"):
            # Get available options
            personas = ['neutral', 'advocate', 'critic', 'philosopher', 'storyteller']
            namespaces = ['lamish-galaxy', 'medieval-realm', 'corporate-dystopia', 
                         'natural-world', 'quantum-realm']
            styles = ['standard', 'academic', 'poetic', 'technical', 'casual']
            
            persona = Prompt.ask(
                "[cyan]Choose persona[/cyan]",
                choices=personas,
                default=suggested_persona
            )
            namespace = Prompt.ask(
                "[cyan]Choose namespace[/cyan]",
                choices=namespaces,
                default=suggested_namespace
            )
            style = Prompt.ask(
                "[cyan]Choose style[/cyan]",
                choices=styles,
                default=suggested_style
            )
        else:
            persona = suggested_persona
            namespace = suggested_namespace
            style = suggested_style
        
        # Create enriched narrative
        enriched_narrative = self._create_enriched_narrative()
        
        # Run projection
        self.console.print("\n[bold]Creating Allegorical Projection...[/bold]")
        self.console.print("[dim]Using insights from dialogue to inform the transformation.[/dim]\n")
        
        try:
            chain = TranslationChain(persona, namespace, style, self.console, verbose=True)
            projection = chain.run(enriched_narrative, show_steps=True)
            
            # Store projection reference in session
            self.session.extracted_elements['projection'] = {
                'persona': persona,
                'namespace': namespace,
                'style': style,
                'projection_id': projection.id
            }
            
            self.console.print("\n[green]✓ Projection complete![/green]")
            self.console.print("[dim]The projection incorporated insights from your dialogue.[/dim]")
            
        except Exception as e:
            self.console.print(f"\n[red]Projection failed: {e}[/red]")
    
    def _suggest_configuration(self) -> Tuple[str, str, str]:
        """Suggest projection configuration based on dialogue insights."""
        if not self.session or not self.session.turns:
            return 'neutral', 'lamish-galaxy', 'standard'
        
        # Analyze dialogue content to suggest configuration
        system_prompt = """Based on a maieutic dialogue, suggest the most appropriate configuration 
for an allegorical projection. Consider the themes, depth, and insights discovered."""
        
        dialogue_summary = f"""Narrative: {self.session.initial_narrative}

Key insights discovered:
"""
        for turn in self.session.turns:
            for insight in turn.insights:
                dialogue_summary += f"- {insight}\n"
        
        dialogue_summary += f"\nFinal understanding: {self.session.final_understanding}"
        
        prompt = f"""{dialogue_summary}

Based on this dialogue, suggest ONE configuration from each category:
Persona: neutral, advocate, critic, philosopher, storyteller
Namespace: lamish-galaxy, medieval-realm, corporate-dystopia, natural-world, quantum-realm  
Style: standard, academic, poetic, technical, casual

Respond with only three words separated by commas: persona,namespace,style"""
        
        try:
            response = self.provider.generate(prompt, system_prompt)
            parts = response.strip().lower().split(',')
            if len(parts) == 3:
                persona = parts[0].strip()
                namespace = parts[1].strip()
                style = parts[2].strip()
                
                # Validate suggestions
                valid_personas = ['neutral', 'advocate', 'critic', 'philosopher', 'storyteller']
                valid_namespaces = ['lamish-galaxy', 'medieval-realm', 'corporate-dystopia', 
                                  'natural-world', 'quantum-realm']
                valid_styles = ['standard', 'academic', 'poetic', 'technical', 'casual']
                
                if persona in valid_personas and namespace in valid_namespaces and style in valid_styles:
                    return persona, namespace, style
        except:
            pass
        
        # Default fallback based on simple heuristics
        if any('conflict' in str(turn.insights).lower() for turn in self.session.turns):
            return 'critic', 'corporate-dystopia', 'technical'
        elif any('meaning' in str(turn.insights).lower() for turn in self.session.turns):
            return 'philosopher', 'quantum-realm', 'poetic'
        else:
            return 'neutral', 'lamish-galaxy', 'standard'
    
    def _create_enriched_narrative(self) -> str:
        """Create an enriched narrative that includes dialogue insights."""
        enriched = f"""ORIGINAL NARRATIVE TO TRANSFORM:
{self.session.initial_narrative}

KEY ELEMENTS TO PRESERVE IN THE ALLEGORY:"""
        
        # Extract the most important discovered elements
        key_elements = []
        
        # Look for specific discoveries about actors, actions, conflicts
        for turn in self.session.turns:
            if "individual" in turn.answer.lower() or "vision" in turn.answer.lower():
                key_elements.append("- Individual with strong personal vision vs institutional expectations")
            if "dropped out" in turn.answer.lower() or "leave" in turn.answer.lower():
                key_elements.append("- Leaving established institution for personal path")
            if "funding" in turn.answer.lower() or "million" in turn.answer.lower():
                key_elements.append("- Early validation through significant resources/support")
        
        # Add discovered themes
        enriched += "\n".join(list(dict.fromkeys(key_elements)))  # Remove duplicates
        
        # Add the core tension identified
        enriched += "\n\nCORE THEME TO EMPHASIZE:"
        enriched += "\nThe universal tension between individual innovation and established structures."
        
        # Add specific insights that should influence the telling
        if self.session.final_understanding:
            enriched += f"\n\nNARRATIVE FOCUS:\n{self.session.final_understanding[:200]}..."
        
        enriched += "\n\nREMEMBER: Create an allegory that tells THE SAME STORY with different characters/settings."
        
        return enriched
    
    def save_session(self, filename: str):
        """Save session to JSON file."""
        if not self.session:
            return
        
        with open(filename, 'w') as f:
            json.dump(self.session.to_dict(), f, indent=2)
        
        self.console.print(f"[green]Session saved to {filename}[/green]")
    
    def load_session(self, filename: str) -> MaieuticSession:
        """Load session from JSON file."""
        with open(filename, 'r') as f:
            data = json.load(f)
        
        session = MaieuticSession(
            id=data.get('id'),
            initial_narrative=data['initial_narrative'],
            goal=data['goal'],
            final_understanding=data.get('final_understanding', ''),
            created_at=datetime.fromisoformat(data['created_at'])
        )
        
        for turn_data in data['turns']:
            turn = DialogueTurn(
                question=turn_data['question'],
                answer=turn_data['answer'],
                insights=turn_data.get('insights', []),
                depth_level=turn_data.get('depth_level', 0),
                timestamp=datetime.fromisoformat(turn_data['timestamp'])
            )
            session.turns.append(turn)
        
        session.extracted_elements = data.get('extracted_elements', {})
        self.session = session
        return session


def run_maieutic_dialogue():
    """Run an interactive maieutic dialogue session."""
    console = Console()
    
    console.print(Panel.fit(
        "[bold]Maieutic Dialogue System[/bold]\n"
        "[dim]Discover deeper truths through guided questioning[/dim]\n"
        "[dim]Then create an informed allegorical projection[/dim]",
        border_style="cyan"
    ))
    
    # Get narrative
    console.print("\n[bold]Enter your narrative:[/bold]")
    console.print("[dim](Press Ctrl+D when finished)[/dim]\n")
    
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    
    narrative = '\n'.join(lines).strip()
    
    if not narrative:
        console.print("[red]No narrative provided.[/red]")
        return
    
    # Create dialogue system
    dialogue = MaieuticDialogue(console)
    
    # Start session
    goal = Prompt.ask(
        "\n[cyan]What would you like to explore?[/cyan]",
        choices=["understand", "clarify", "discover", "question"],
        default="understand"
    )
    
    dialogue.start_session(narrative, goal)
    
    # Conduct dialogue
    max_turns = Prompt.ask(
        "[cyan]How many rounds of questions?[/cyan]",
        default="5"
    )
    
    try:
        max_turns = int(max_turns)
    except:
        max_turns = 5
    
    # Note: auto_project=True by default, will offer projection after dialogue
    session = dialogue.conduct_dialogue(max_turns, auto_project=True)
    
    # Offer to save
    if Confirm.ask("\n[cyan]Save this dialogue session?[/cyan]"):
        filename = Prompt.ask(
            "[cyan]Filename[/cyan]",
            default=f"maieutic_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        dialogue.save_session(filename)


if __name__ == "__main__":
    run_maieutic_dialogue()