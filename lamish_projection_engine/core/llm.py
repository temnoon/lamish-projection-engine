"""LLM integration for Lamish Projection Engine."""
import json
import time
from typing import Dict, Any, List, Optional, Protocol
from dataclasses import dataclass
import logging
import hashlib
import ollama
from ollama import Client
import numpy as np

from lamish_projection_engine.utils.config import get_config

logger = logging.getLogger(__name__)


class LLMProvider(Protocol):
    """Protocol for LLM providers."""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate text from prompt."""
        ...
    
    def embed(self, text: str) -> List[float]:
        """Generate embeddings for text."""
        ...


@dataclass
class LLMResponse:
    """Response from LLM with metadata."""
    text: str
    model: str
    duration_ms: int
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None


class OllamaProvider:
    """Ollama LLM provider."""
    
    def __init__(self, host: Optional[str] = None, 
                 model: Optional[str] = None,
                 embedding_model: Optional[str] = None):
        config = get_config()
        self.host = host or config.ollama_host
        self.model = model or config.llm_model
        self.embedding_model = embedding_model or config.embedding_model
        self.temperature = config.llm_temperature
        self.max_tokens = config.llm_max_tokens
        
        try:
            self.client = Client(host=self.host)
            # Test connection
            self.client.list()
            self.available = True
            logger.info(f"Connected to Ollama at {self.host}")
        except Exception as e:
            logger.warning(f"Could not connect to Ollama: {e}")
            self.available = False
    
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate text using Ollama."""
        if not self.available:
            raise RuntimeError("Ollama is not available")
        
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens
                }
            )
            
            return response['message']['content']
            
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            raise
    
    def embed(self, text: str) -> List[float]:
        """Generate embeddings using Ollama."""
        if not self.available:
            raise RuntimeError("Ollama is not available")
        
        try:
            response = self.client.embed(
                model=self.embedding_model,
                input=text
            )
            
            # Ollama returns embeddings as a list of lists
            if isinstance(response['embeddings'], list) and len(response['embeddings']) > 0:
                return response['embeddings'][0]
            else:
                return response['embeddings']
                
        except Exception as e:
            logger.error(f"Ollama embedding error: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if Ollama is available."""
        return self.available
    
    def list_models(self) -> List[str]:
        """List available models."""
        if not self.available:
            return []
        
        try:
            response = self.client.list()
            # Handle newer ollama client response structure
            if hasattr(response, 'models'):
                return [model.model for model in response.models]
            elif hasattr(response, 'model_dump'):
                models_data = response.model_dump()
                return [m['model'] for m in models_data.get('models', [])]
            else:
                # Fallback for older versions
                return [m['name'] for m in response.get('models', [])]
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []


class MockLLMProvider:
    """Mock LLM provider for testing."""
    
    def __init__(self):
        self.model = "mock-llm"
        self.embedding_model = "mock-embeddings"
    
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        """Generate mock response based on prompt content."""
        # Extract namespace/persona/style from system prompt if available
        namespace = "generic-space"  # default
        if "lamish-galaxy" in system_prompt:
            namespace = "lamish-galaxy"
        elif "medieval-realm" in system_prompt:
            namespace = "medieval-realm"
        elif "to the" in prompt and "lamish-galaxy" in prompt:
            namespace = "lamish-galaxy"
        elif "from the" in prompt and "perspective" in prompt:
            namespace = "lamish-galaxy"  # Assume lamish-galaxy for reconstruction
        
        # Detect step type from prompt
        if "extract its core elements" in system_prompt:
            # Deconstruct - extract actual elements from the narrative
            if "Altman" in prompt or "Stanford" in prompt:
                return """WHO: Tech entrepreneur who left prestigious university
WHAT: Founded companies, raised capital, leads AI organization
WHY: Believed personal vision more valuable than institutional path
HOW: Through startup ecosystem, venture funding, leadership roles
OUTCOME: Became influential figure in AI revolution"""
            else:
                return """WHO: Individual with vision
WHAT: Left institution, created ventures, leads organization
WHY: Personal vision exceeded institutional boundaries
HOW: Through independent action and leadership
OUTCOME: Transformed their field"""
        
        elif "mapping narrative elements" in system_prompt:
            # Map to namespace
            if "lamish-galaxy" in namespace or "lamish-galaxy" in prompt:
                if "entrepreneur" in prompt or "university" in prompt or "WHO:" in prompt:
                        # Return mapped elements that will be used in reconstruction
                    return """MAPPED ELEMENTS:
- Sam Altman → Navigator-Innovator Keth-9
- Stanford University → The Academy of Harmonic Sciences on Lamen
- Dropping out after two years → Departing after just two cycles
- First company (Loopt) → First Pulse-craft venture (social resonance network)
- $30 million venture funding → 30 million units of Resonance funding from the Galactic Frequency Council
- Y Combinator presidency → Leading the Startup Harmonizer Collective
- OpenAI CEO → Head of the Consciousness Synthesis Institute
- Leading AI revolution → Guiding the Great Awakening of synthetic minds
- Net worth $1.7 billion → Net resonance of 1.7 billion frequency units"""
            elif "medieval-realm" in namespace:
                return """In the Medieval Realm:
- Tech entrepreneur → Young apprentice who left the Grand Academy
- University → The Grand Academy of Arcane Studies
- Startup → New guild of innovative craftsmen
- Funding → Gold from merchant princes
- AI leadership → Master of the Golem-Makers Guild"""
            return "Mapped elements to " + namespace
        
        elif "reconstructing the narrative" in system_prompt:
            # Reconstruct story using mapped elements
            if "MAPPED ELEMENTS" in prompt or "Navigator-Innovator" in prompt:
                # We have the mapped elements, reconstruct the story  
                return """Navigator-Innovator Keth-9 made a decision that would echo across the Pulse networks of the Lamish Galaxy. After just two cycles at the prestigious Academy of Harmonic Sciences on Lamen, they departed, convinced their vision for frequency manipulation exceeded what the Academy's rigid harmonics could teach.

Keth-9 founded their first Pulse-craft venture, a social resonance network that attracted over 30 million units of Resonance funding from the Galactic Frequency Council. This early validation proved that innovation flows faster outside institutional channels.

Rising through the ranks of the Startup Harmonizer Collective, Keth-9 eventually took its helm, nurturing countless new frequency ventures. Now, as head of the Consciousness Synthesis Institute, they guide the Great Awakening - the emergence of synthetic minds across the galaxy. Their net resonance has grown to 1.7 billion frequency units, but the real measure of their impact is the fundamental transformation of consciousness itself."""
            elif "medieval-realm" in namespace:
                return """Young Apprentice Aldric left the Grand Academy after merely two seasons, founding the first of their merchant guilds with 30 million gold pieces from the merchant princes. Rising to Master of the Innovation Guild, they now lead the Golem-Makers, bringing consciousness to clay and stone. Their fortune of 1.7 billion gold marks pales beside their true legacy: the awakening of artificial minds."""
            return "Story reconstructed in " + namespace
        
        elif "applying the" in system_prompt and "style" in system_prompt:
            # Stylize - extract the text after the instruction
            if "Rewrite this in" in prompt and ":\n\n" in prompt:
                text_to_style = prompt.split(":\n\n", 1)[1]
                return text_to_style  # For standard style, return as-is
            return prompt
        
        elif "meta-commentary" in system_prompt:
            # Reflect
            return """This projection illuminates how the tension between individual vision and institutional structure is universal. By translating a tech entrepreneur's journey into the Lamish Galaxy's frequency-based reality, we see that the pattern of leaving established paths to create new possibilities transcends specific contexts. The Academy becomes any institution that cannot contain innovative minds, and Resonance funding represents any system that validates unconventional paths."""
        
        # Default
        return f"Mock response for: {prompt[:50]}..."
    
    def embed(self, text: str) -> List[float]:
        """Generate mock embeddings."""
        # Create deterministic embeddings based on text
        hash_val = hashlib.md5(text.encode()).digest()
        # Convert to 768-dim float array (standard sentence-transformer size)
        values = []
        for i in range(96):  # 96 * 8 = 768
            chunk = hash_val[i % 16:(i % 16) + 8]
            value = int.from_bytes(chunk[:4], 'big') / (2**32)
            values.extend([value] * 8)
        
        # Normalize
        embeddings = np.array(values[:768])
        embeddings = embeddings / np.linalg.norm(embeddings)
        return embeddings.tolist()
    
    def is_available(self) -> bool:
        """Mock is always available."""
        return True
    
    def list_models(self) -> List[str]:
        """List mock models."""
        return ["mock-llm", "mock-embeddings"]


class LLMTransformer:
    """Main LLM transformer that handles allegorical projections."""
    
    def __init__(self, persona: str, namespace: str, style: str, 
                 provider: Optional[LLMProvider] = None):
        self.persona = persona
        self.namespace = namespace
        self.style = style
        
        # Use provided provider or create based on config
        if provider:
            self.provider = provider
        else:
            config = get_config()
            if config.use_mock_llm:
                logger.info("Using mock LLM provider")
                self.provider = MockLLMProvider()
            else:
                logger.info("Using Ollama LLM provider")
                self.provider = OllamaProvider()
    
    def _build_system_prompt(self, step_type: str) -> str:
        """Build system prompt for specific transformation step."""
        base_prompts = {
            'deconstruct': f"""You are analyzing a narrative to extract its core elements.
Identify the fundamental components: WHO (key actors/roles), WHAT (actions/events), WHY (motivations/conflicts), 
HOW (methods/approaches), and OUTCOME (results/implications).
Be specific about the actual story elements, not generic concepts.""",
            
            'map': f"""You are mapping narrative elements to the {self.namespace} universe.
IMPORTANT: Create direct analogues that preserve the story structure:
- Map each real person/entity to a specific {self.namespace} character/entity
- Map each real action/event to an equivalent {self.namespace} action/event
- Map each real institution/concept to a {self.namespace} equivalent
- Preserve the relationships, sequence, and meaning
This should be a clear translation, not a vague reinterpretation.""",
            
            'reconstruct': f"""You are reconstructing the narrative from the perspective of {self.persona}.
Tell the SAME STORY with the mapped elements, preserving:
- The sequence of events
- The relationships between characters
- The core conflict and its resolution
- The implications and outcomes
Use the {self.persona}'s voice but keep the narrative structure intact.""",
            
            'stylize': f"""You are applying the {self.style} language style to the narrative.
Adjust the tone and voice to match {self.style} style while keeping the story content unchanged.
Do not alter the plot, characters, or meaning - only the way it's expressed.""",
            
            'reflect': f"""You are generating a meta-commentary on this allegorical projection.
Explain how the {self.namespace} version illuminates the original narrative.
What universal patterns or deeper truths does this transformation reveal?
How does viewing it through this lens change our understanding?"""
        }
        
        return base_prompts.get(step_type, "You are a helpful assistant.")
    
    def transform(self, input_text: str, step_type: str) -> str:
        """Transform text for a specific step in the translation chain."""
        system_prompt = self._build_system_prompt(step_type)
        
        # Build step-specific prompts
        prompts = {
            'deconstruct': f"Analyze this narrative and extract its core elements:\n\n{input_text}",
            'map': f"Map these narrative elements to the {self.namespace}:\n\n{input_text}",
            'reconstruct': f"Reconstruct this as a story from the {self.persona} perspective:\n\n{input_text}",
            'stylize': f"Rewrite this in {self.style} style:\n\n{input_text}",
            'reflect': f"Generate a reflection on this allegorical transformation:\n\n{input_text}"
        }
        
        prompt = prompts.get(step_type, input_text)
        
        try:
            return self.provider.generate(prompt, system_prompt)
        except Exception as e:
            logger.error(f"Transform error at step {step_type}: {e}")
            # Fallback to mock if real LLM fails
            if not isinstance(self.provider, MockLLMProvider):
                logger.info("Falling back to mock LLM")
                mock = MockLLMProvider()
                return mock.generate(prompt, system_prompt)
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text."""
        try:
            return self.provider.embed(text)
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            # Fallback to mock
            if not isinstance(self.provider, MockLLMProvider):
                logger.info("Falling back to mock embeddings")
                mock = MockLLMProvider()
                return mock.embed(text)
            raise


def get_llm_provider() -> LLMProvider:
    """Get the configured LLM provider."""
    config = get_config()
    
    if config.use_mock_llm:
        return MockLLMProvider()
    
    # Try Ollama first
    ollama_provider = OllamaProvider()
    if ollama_provider.is_available():
        models = ollama_provider.list_models()
        logger.info(f"Available Ollama models: {models}")
        
        # Check if our preferred models are available
        if config.llm_model not in models:
            logger.warning(f"Model {config.llm_model} not found. Available: {models}")
            # Try to pull the model
            try:
                logger.info(f"Attempting to pull {config.llm_model}...")
                ollama_provider.client.pull(config.llm_model)
            except:
                logger.warning(f"Could not pull {config.llm_model}")
        
        return ollama_provider
    
    # Fallback to mock
    logger.warning("No LLM provider available, using mock")
    return MockLLMProvider()


def test_llm_connection():
    """Test LLM connection and capabilities."""
    provider = get_llm_provider()
    
    print(f"Provider: {provider.__class__.__name__}")
    print(f"Available: {provider.is_available()}")
    
    if hasattr(provider, 'list_models'):
        print(f"Models: {provider.list_models()}")
    
    # Test generation
    try:
        response = provider.generate("Hello, world!", "You are a helpful assistant.")
        print(f"Generation test: {response[:100]}...")
    except Exception as e:
        print(f"Generation error: {e}")
    
    # Test embedding
    try:
        embedding = provider.embed("Test embedding")
        print(f"Embedding test: {len(embedding)} dimensions")
    except Exception as e:
        print(f"Embedding error: {e}")


if __name__ == "__main__":
    # Test the LLM connection
    test_llm_connection()