"""Dynamic attribute system for LPE configuration."""
import json
import logging
from typing import Dict, Any, List, Optional, Union, Type, get_type_hints
from dataclasses import dataclass, field, fields
from datetime import datetime
from abc import ABC, abstractmethod
from pathlib import Path

from lamish_projection_engine.core.llm import get_llm_provider

logger = logging.getLogger(__name__)


@dataclass
class AttributeField:
    """Represents a configurable field in an attribute."""
    name: str
    value: Any
    field_type: str = "text"  # text, number, boolean, select, textarea, json
    description: str = ""
    options: List[str] = field(default_factory=list)  # For select fields
    generated_by: str = "user"  # user, ai, system
    last_modified: datetime = field(default_factory=datetime.now)
    prompt_template: str = ""  # For AI-generated fields
    is_core: bool = True  # Core fields always present, others can be added/removed
    weight: float = 1.0  # Importance weight for arbitrator


@dataclass 
class PromptContribution:
    """A contribution to the system prompt from an attribute."""
    source: str  # persona, namespace, style, etc.
    content: str
    weight: float = 1.0
    context_dependent: bool = False
    conditions: Dict[str, Any] = field(default_factory=dict)


class DynamicAttribute(ABC):
    """Base class for dynamic, configurable attributes."""
    
    def __init__(self, name: str, config_path: Optional[Path] = None):
        self.name = name
        self.config_path = config_path or Path(f"config/{name.lower()}.json")
        self.fields: Dict[str, AttributeField] = {}
        self.prompt_templates: Dict[str, str] = {}
        self.version = "1.0"
        self.llm_provider = get_llm_provider()
        
        # Load configuration if exists
        if self.config_path.exists():
            self.load_config()
        else:
            self._initialize_default_fields()
    
    @abstractmethod
    def _initialize_default_fields(self):
        """Initialize the default fields for this attribute type."""
        pass
    
    @abstractmethod
    def generate_prompt_contribution(self, context: Dict[str, Any] = None) -> PromptContribution:
        """Generate this attribute's contribution to the system prompt."""
        pass
    
    def add_field(self, field: AttributeField):
        """Add a new field to this attribute."""
        self.fields[field.name] = field
        logger.info(f"Added field '{field.name}' to {self.name}")
    
    def remove_field(self, field_name: str) -> bool:
        """Remove a field (only non-core fields can be removed)."""
        if field_name in self.fields and not self.fields[field_name].is_core:
            del self.fields[field_name]
            logger.info(f"Removed field '{field_name}' from {self.name}")
            return True
        return False
    
    def update_field(self, field_name: str, value: Any, updated_by: str = "user"):
        """Update a field value."""
        if field_name in self.fields:
            self.fields[field_name].value = value
            self.fields[field_name].last_modified = datetime.now()
            self.fields[field_name].generated_by = updated_by
            logger.info(f"Updated field '{field_name}' in {self.name}")
    
    def generate_field_with_ai(self, field_name: str, prompt_template: str, context: Dict[str, Any] = None):
        """Generate or update a field using AI."""
        try:
            # Build prompt with context
            context = context or {}
            context.update({f.name: f.value for f in self.fields.values()})
            
            prompt = prompt_template.format(**context)
            system_prompt = f"""You are configuring a {self.__class__.__name__} for the Lamish Projection Engine.
Generate a value for the field '{field_name}' based on the current configuration and context.
Return only the value, no explanation."""
            
            value = self.llm_provider.generate(prompt, system_prompt)
            
            # Create or update field
            if field_name in self.fields:
                self.update_field(field_name, value.strip(), "ai")
            else:
                new_field = AttributeField(
                    name=field_name,
                    value=value.strip(),
                    generated_by="ai",
                    prompt_template=prompt_template,
                    is_core=False
                )
                self.add_field(new_field)
                
        except Exception as e:
            logger.error(f"Failed to generate field '{field_name}' with AI: {e}")
    
    def save_config(self):
        """Save configuration to file."""
        config = {
            "name": self.name,
            "version": self.version,
            "fields": {
                name: {
                    "value": field.value,
                    "field_type": field.field_type,
                    "description": field.description,
                    "options": field.options,
                    "generated_by": field.generated_by,
                    "last_modified": field.last_modified.isoformat(),
                    "prompt_template": field.prompt_template,
                    "is_core": field.is_core,
                    "weight": field.weight
                }
                for name, field in self.fields.items()
            },
            "prompt_templates": self.prompt_templates
        }
        
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Saved {self.name} configuration to {self.config_path}")
    
    def load_config(self):
        """Load configuration from file."""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            self.version = config.get("version", "1.0")
            self.prompt_templates = config.get("prompt_templates", {})
            
            for name, field_data in config.get("fields", {}).items():
                field = AttributeField(
                    name=name,
                    value=field_data["value"],
                    field_type=field_data.get("field_type", "text"),
                    description=field_data.get("description", ""),
                    options=field_data.get("options", []),
                    generated_by=field_data.get("generated_by", "user"),
                    last_modified=datetime.fromisoformat(field_data.get("last_modified", datetime.now().isoformat())),
                    prompt_template=field_data.get("prompt_template", ""),
                    is_core=field_data.get("is_core", True),
                    weight=field_data.get("weight", 1.0)
                )
                self.fields[name] = field
                
            logger.info(f"Loaded {self.name} configuration from {self.config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load configuration for {self.name}: {e}")
            self._initialize_default_fields()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "name": self.name,
            "version": self.version,
            "fields": {
                name: {
                    "value": field.value,
                    "field_type": field.field_type,
                    "description": field.description,
                    "options": field.options,
                    "generated_by": field.generated_by,
                    "last_modified": field.last_modified.isoformat(),
                    "is_core": field.is_core,
                    "weight": field.weight
                }
                for name, field in self.fields.items()
            }
        }


class PersonaAttribute(DynamicAttribute):
    """Dynamic persona configuration."""
    
    def _initialize_default_fields(self):
        """Initialize default persona fields."""
        self.fields = {
            "base_type": AttributeField(
                name="base_type",
                value="neutral",
                field_type="select",
                description="Base persona type",
                options=["neutral", "advocate", "critic", "philosopher", "storyteller", "scientist", "artist"],
                is_core=True
            ),
            "perspective": AttributeField(
                name="perspective",
                value="balanced",
                field_type="select", 
                description="Narrative perspective approach",
                options=["balanced", "optimistic", "skeptical", "analytical", "emotional", "detached"],
                is_core=True
            ),
            "voice_style": AttributeField(
                name="voice_style",
                value="clear and direct",
                field_type="text",
                description="Characteristic voice and tone",
                is_core=True
            ),
            "expertise_domains": AttributeField(
                name="expertise_domains",
                value="general knowledge",
                field_type="textarea",
                description="Areas of specialized knowledge or interest",
                is_core=True
            ),
            "bias_tendencies": AttributeField(
                name="bias_tendencies",
                value="minimal bias",
                field_type="textarea", 
                description="Known biases or tendencies in interpretation",
                is_core=True
            )
        }
        
        self.prompt_templates = {
            "expertise_domains": "Based on the persona type '{base_type}' and perspective '{perspective}', what expertise domains would this persona naturally have?",
            "voice_style": "What voice style would be characteristic of a {base_type} persona with a {perspective} perspective?",
            "contextual_modifier": "Given the current narrative about {narrative_topic}, how should this {base_type} persona's approach be modified?"
        }
    
    def generate_prompt_contribution(self, context: Dict[str, Any] = None) -> PromptContribution:
        """Generate persona's contribution to the system prompt."""
        base_type = self.fields.get("base_type", AttributeField("", "neutral")).value
        perspective = self.fields.get("perspective", AttributeField("", "balanced")).value
        voice_style = self.fields.get("voice_style", AttributeField("", "clear")).value
        expertise = self.fields.get("expertise_domains", AttributeField("", "general")).value
        biases = self.fields.get("bias_tendencies", AttributeField("", "minimal")).value
        
        content = f"""PERSONA CONFIGURATION:
You are adopting the perspective of a {base_type} with a {perspective} approach.

Voice Style: {voice_style}
Expertise Domains: {expertise}
Bias Awareness: {biases}

When transforming narratives, maintain this persona's characteristic viewpoint while preserving the core meaning."""

        # Add any dynamic fields
        for name, field in self.fields.items():
            if not field.is_core and field.weight > 0.5:
                content += f"\n{field.description}: {field.value}"
        
        return PromptContribution(
            source="persona",
            content=content,
            weight=sum(f.weight for f in self.fields.values()) / len(self.fields)
        )


class NamespaceAttribute(DynamicAttribute):
    """Dynamic namespace configuration."""
    
    def _initialize_default_fields(self):
        """Initialize default namespace fields."""
        self.fields = {
            "base_setting": AttributeField(
                name="base_setting",
                value="lamish-galaxy",
                field_type="select",
                description="Base narrative setting",
                options=["lamish-galaxy", "medieval-realm", "corporate-dystopia", "natural-world", "quantum-realm", "steampunk-era", "cyberpunk-future"],
                is_core=True
            ),
            "core_metaphors": AttributeField(
                name="core_metaphors",
                value="frequency networks, harmonic resonance, pulse-craft",
                field_type="textarea",
                description="Key metaphors and concepts specific to this namespace",
                is_core=True
            ),
            "power_structures": AttributeField(
                name="power_structures",
                value="Galactic Frequency Council, Academy hierarchies",
                field_type="textarea",
                description="How power and authority work in this universe",
                is_core=True
            ),
            "technology_level": AttributeField(
                name="technology_level",
                value="advanced harmonic manipulation",
                field_type="text",
                description="Characteristic technology and capabilities",
                is_core=True
            ),
            "social_dynamics": AttributeField(
                name="social_dynamics",
                value="resonance-based social networks",
                field_type="textarea",
                description="How relationships and social structures function",
                is_core=True
            ),
            "conflict_patterns": AttributeField(
                name="conflict_patterns",
                value="innovation vs tradition, individual vs collective harmony",
                field_type="textarea",
                description="Common sources of tension and conflict",
                is_core=True
            )
        }
        
        self.prompt_templates = {
            "core_metaphors": "For a {base_setting} setting, what metaphors would best represent {concept_type}?",
            "power_structures": "In a {base_setting} universe, how would power and authority typically be organized?",
            "technology_level": "What level and type of technology would fit a {base_setting} narrative universe?",
            "mapping_rules": "How should {real_world_element} be translated into the {base_setting} universe?"
        }
    
    def generate_prompt_contribution(self, context: Dict[str, Any] = None) -> PromptContribution:
        """Generate namespace's contribution to the system prompt."""
        base_setting = self.fields.get("base_setting", AttributeField("", "generic")).value
        metaphors = self.fields.get("core_metaphors", AttributeField("", "")).value
        power_structures = self.fields.get("power_structures", AttributeField("", "")).value
        technology = self.fields.get("technology_level", AttributeField("", "")).value
        social_dynamics = self.fields.get("social_dynamics", AttributeField("", "")).value
        conflicts = self.fields.get("conflict_patterns", AttributeField("", "")).value
        
        content = f"""NAMESPACE CONFIGURATION:
Target Universe: {base_setting}

Core Metaphors: {metaphors}
Power Structures: {power_structures}
Technology Level: {technology}
Social Dynamics: {social_dynamics}
Conflict Patterns: {conflicts}

When mapping elements to this namespace, use these established patterns and metaphors to maintain consistency."""

        return PromptContribution(
            source="namespace",
            content=content,
            weight=sum(f.weight for f in self.fields.values()) / len(self.fields)
        )


class LanguageStyleAttribute(DynamicAttribute):
    """Dynamic language style configuration."""
    
    def _initialize_default_fields(self):
        """Initialize default language style fields."""
        self.fields = {
            "base_style": AttributeField(
                name="base_style",
                value="standard",
                field_type="select",
                description="Base language style",
                options=["standard", "academic", "poetic", "technical", "casual", "formal", "archaic", "futuristic"],
                is_core=True
            ),
            "formality_level": AttributeField(
                name="formality_level",
                value="medium",
                field_type="select",
                description="Level of formality",
                options=["very_casual", "casual", "medium", "formal", "very_formal"],
                is_core=True
            ),
            "sentence_structure": AttributeField(
                name="sentence_structure",
                value="varied",
                field_type="select",
                description="Preferred sentence structure patterns",
                options=["simple", "compound", "complex", "varied", "rhythmic"],
                is_core=True
            ),
            "vocabulary_level": AttributeField(
                name="vocabulary_level",
                value="accessible",
                field_type="select",
                description="Vocabulary complexity",
                options=["simple", "accessible", "elevated", "technical", "archaic"],
                is_core=True
            ),
            "rhetorical_devices": AttributeField(
                name="rhetorical_devices",
                value="metaphor, analogy",
                field_type="textarea",
                description="Preferred rhetorical devices and literary techniques",
                is_core=True
            ),
            "cultural_markers": AttributeField(
                name="cultural_markers",
                value="universal concepts",
                field_type="textarea",
                description="Cultural references and linguistic markers to include/avoid",
                is_core=True
            )
        }
        
        self.prompt_templates = {
            "rhetorical_devices": "What rhetorical devices would work best for {base_style} style writing?",
            "cultural_markers": "For {base_style} style in a {namespace} setting, what cultural markers should be used?",
            "adaptation_rules": "How should {base_style} style be adapted for {content_type} content?"
        }
    
    def generate_prompt_contribution(self, context: Dict[str, Any] = None) -> PromptContribution:
        """Generate language style's contribution to the system prompt."""
        base_style = self.fields.get("base_style", AttributeField("", "standard")).value
        formality = self.fields.get("formality_level", AttributeField("", "medium")).value
        structure = self.fields.get("sentence_structure", AttributeField("", "varied")).value
        vocabulary = self.fields.get("vocabulary_level", AttributeField("", "accessible")).value
        rhetoric = self.fields.get("rhetorical_devices", AttributeField("", "")).value
        culture = self.fields.get("cultural_markers", AttributeField("", "")).value
        
        content = f"""LANGUAGE STYLE CONFIGURATION:
Base Style: {base_style}
Formality Level: {formality}
Sentence Structure: {structure}
Vocabulary Level: {vocabulary}
Rhetorical Devices: {rhetoric}
Cultural Markers: {culture}

Apply this style consistently while preserving narrative meaning and structure."""

        return PromptContribution(
            source="language_style",
            content=content,
            weight=sum(f.weight for f in self.fields.values()) / len(self.fields)
        )


class ConfigurationManager:
    """Manages all dynamic attributes and their configurations."""
    
    def __init__(self, config_dir: Path = Path("config")):
        self.config_dir = config_dir
        self.config_dir.mkdir(exist_ok=True)
        
        self.attributes: Dict[str, DynamicAttribute] = {}
        self.llm_provider = get_llm_provider()
        
        # Initialize default attributes
        self._initialize_default_attributes()
    
    def _initialize_default_attributes(self):
        """Initialize the three core attribute types."""
        self.attributes = {
            "persona": PersonaAttribute("persona", self.config_dir / "persona.json"),
            "namespace": NamespaceAttribute("namespace", self.config_dir / "namespace.json"),
            "language_style": LanguageStyleAttribute("language_style", self.config_dir / "language_style.json")
        }
    
    def get_attribute(self, name: str) -> Optional[DynamicAttribute]:
        """Get an attribute by name."""
        return self.attributes.get(name)
    
    def create_custom_attribute(self, name: str, base_class: Type[DynamicAttribute]) -> DynamicAttribute:
        """Create a new custom attribute."""
        attr = base_class(name, self.config_dir / f"{name}.json")
        self.attributes[name] = attr
        return attr
    
    def save_all_configurations(self):
        """Save all attribute configurations."""
        for attr in self.attributes.values():
            attr.save_config()
    
    def generate_system_prompt(self, context: Dict[str, Any] = None) -> str:
        """Generate the complete system prompt from all attributes."""
        contributions = []
        
        for attr in self.attributes.values():
            contribution = attr.generate_prompt_contribution(context)
            contributions.append(contribution)
        
        # Use arbitrator to decide what to include
        arbitrated_prompt = self._arbitrate_prompt_contributions(contributions, context)
        
        return arbitrated_prompt
    
    def _arbitrate_prompt_contributions(self, contributions: List[PromptContribution], context: Dict[str, Any] = None) -> str:
        """Use AI arbitrator to decide what to include in the final prompt."""
        try:
            # Build arbitration prompt
            contribution_summaries = []
            for i, contrib in enumerate(contributions):
                summary = f"Source {i+1} ({contrib.source}): Weight {contrib.weight:.2f}\n{contrib.content[:200]}..."
                contribution_summaries.append(summary)
            
            arbitration_prompt = f"""You are the prompt arbitrator for the Lamish Projection Engine.
Given these potential contributions to the system prompt, decide which elements to include and how to combine them effectively.

Context: {context or "No specific context"}

Available contributions:
{chr(10).join(contribution_summaries)}

Create a coherent, effective system prompt that includes the most relevant elements without being overly verbose.
Focus on elements that will help create meaningful allegorical transformations."""

            system_prompt = """You are a prompt arbitrator. Create clear, effective system prompts by selecting and combining the most relevant elements."""
            
            arbitrated = self.llm_provider.generate(arbitration_prompt, system_prompt)
            return arbitrated
            
        except Exception as e:
            logger.error(f"Arbitration failed: {e}")
            # Fallback: combine all contributions
            return "\n\n".join(contrib.content for contrib in contributions)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert all configurations to dictionary for API."""
        return {
            name: attr.to_dict() 
            for name, attr in self.attributes.items()
        }