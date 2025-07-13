# Lamish Projection Engine - Advanced Features Guide

## Quick Start

### 🚀 Simple Startup Script
```bash
# Quick web server
python start_lpe.py web

# View current configuration
python start_lpe.py config

# Run feature tests
python start_lpe.py test

# Test translation analysis
python start_lpe.py roundtrip
```

### 🖥️ Full CLI Commands
```bash
# Start web server
python -m lamish_projection_engine.cli.main web

# Interactive configuration
python -m lamish_projection_engine.cli.main config

# Round-trip translation analysis
python -m lamish_projection_engine.cli.main roundtrip

# Create projections
python -m lamish_projection_engine.cli.main project

# Socratic dialogue
python -m lamish_projection_engine.cli.main maieutic
```

## 🎛️ Dynamic Configuration System

### Core Concept
The LPE now uses a **trinity of fluid attributes** that define how narratives are transformed:

1. **Persona** - The narrative perspective and voice
2. **Namespace** - The fictional universe for projection  
3. **Language Style** - The rhetorical and linguistic approach

### Key Features
- **Fluid Fields**: Add, remove, or modify any field in any attribute
- **AI Generation**: Fields can be automatically generated using LLM prompts
- **User/AI Control**: Both humans and AI agents can modify configurations
- **Arbitrator AI**: Intelligent system decides what to include in final prompts
- **Persistence**: All configurations are saved and can be reloaded

### Example Usage
```python
from lamish_projection_engine.config.dynamic_attributes import ConfigurationManager

# Create configuration manager
config_manager = ConfigurationManager()

# Get an attribute
persona = config_manager.get_attribute("persona")

# Modify a field
persona.update_field("voice_style", "analytical and precise", "user")

# Add a new AI-generated field
persona.generate_field_with_ai(
    "contextual_insight",
    "Based on the persona type '{base_type}', what insight would be valuable for {narrative_topic}?"
)

# Generate complete system prompt
system_prompt = config_manager.generate_system_prompt({
    "narrative_topic": "technology innovation"
})
```

## 🔄 Back-Translation Analysis

### What It Does
Back-translation reveals the **stable semantic core** of text by:
1. Translating to an intermediate language (Spanish, French, etc.)
2. Translating back to English
3. Analyzing what changed and what remained stable

### Supported Languages
- Spanish, French, German, Italian, Portuguese
- Chinese, Japanese, Korean, Arabic, Hebrew, Hindi
- Dutch, Swedish, Norwegian, Danish, Polish, Czech

### Example Results
```
Original: "Innovation drives technological progress"
Via Spanish: "La innovación impulsa el progreso tecnológico" 
Final: "Innovation drives technological advancement"

Semantic Drift: 15.2%
Preserved: ["innovation concept", "causation relationship", "technology focus"]
Lost: ["progress specificity"]
Gained: ["advancement nuance"]
```

### Use Cases
- **Meaning Analysis**: Find the core concepts that survive translation
- **Cultural Adaptation**: See how ideas change across languages
- **Narrative Stability**: Test which story elements are universal
- **Quality Assurance**: Verify projection meaning preservation

## 🌐 Web Interface (localhost:8000)

### Features
- **Live Configuration**: Edit attributes through web interface
- **Projection Creation**: Create allegorical transformations with visual feedback
- **Translation Analysis**: Perform round-trip analysis via web forms
- **API Access**: Complete REST API for programmatic access

### API Endpoints
```
GET  /api/health              - System health check
GET  /api/config              - Get all configurations
PUT  /api/config/{attr}/{field} - Update attribute field
POST /api/projection/create   - Create new projection
POST /api/translation/round-trip - Round-trip analysis
GET  /api/translation/supported-languages - Available languages
```

### Web Interface Usage
1. Start server: `python start_lpe.py web`
2. Open browser: `http://localhost:8000`
3. Use interface for configuration, projection, and analysis

## 🗄️ Enhanced Database Schema

### New Tables
- **Dynamic Attributes**: Store fluid configuration data
- **Translation Records**: Track all language transformations
- **Maieutic Sessions**: Persistent Socratic dialogue storage
- **Text Versions**: Version control for transformations
- **Arbitrator Decisions**: Record AI prompt composition choices

### Features
- **Full Traceability**: Every change and decision is recorded
- **Performance Metrics**: Timing and token usage tracking
- **Vector Embeddings**: Semantic search capabilities
- **Session Management**: Persistent user sessions

## 🤖 AI Agent Integration

### Configuration Generation
AI agents can dynamically create and modify configurations:

```python
# AI generates field based on context
persona.generate_field_with_ai(
    "narrative_approach",
    "For a {base_type} persona analyzing {content_type}, what approach should be taken?"
)

# AI modifies based on narrative content
namespace.generate_field_with_ai(
    "contextual_mapping",
    "How should {real_element} be represented in {base_setting}?"
)
```

### Arbitrator AI
The system includes an AI arbitrator that:
- Decides which configuration elements to include
- Balances prompt length vs. completeness
- Adapts to context and narrative content
- Records reasoning for decisions

## 🔬 Semantic Analysis Features

### Round-Trip Insights
```python
from lamish_projection_engine.core.translation_roundtrip import LanguageRoundTripAnalyzer

analyzer = LanguageRoundTripAnalyzer()

# Single round-trip
result = analyzer.perform_round_trip(text, "spanish")

# Multi-language stability analysis
stable_core = analyzer.find_stable_meaning_core(text, 
    ["spanish", "french", "german", "chinese"])
```

### Projection Analysis
- **Before/After Comparison**: Compare original vs. allegorical version
- **Element Mapping**: Track how real-world elements become fictional
- **Meaning Preservation**: Measure semantic stability through transformation
- **Cross-Language Validation**: Test projection stability across languages

## 🎯 Advanced Workflows

### 1. AI-Configured Projections
```python
# AI agent configures itself for specific narrative
config_manager = ConfigurationManager()
ai_agent.configure_for_narrative(narrative_text, config_manager)
projection = create_projection_with_config(narrative_text, config_manager)
```

### 2. Semantic Archaeology
```python
# Find what survives multiple transformations
original_text = "Complex narrative about innovation..."
roundtrip_result = analyzer.perform_round_trip(original_text, "spanish")
projection_result = create_projection(roundtrip_result.final_text)
final_roundtrip = analyzer.perform_round_trip(projection_result.final_projection, "french")

# Analyze what core meaning survived all transformations
```

### 3. Cross-Cultural Projection
```python
# Test projection across different cultural lenses
for language in ["spanish", "chinese", "arabic"]:
    cultural_result = analyzer.perform_round_trip(narrative, language)
    cultural_projection = create_projection(cultural_result.final_text)
    # Compare how different cultures interpret the narrative
```

## 🎨 Configuration Examples

### Persona Configurations
```json
{
  "base_type": "philosopher",
  "perspective": "analytical", 
  "voice_style": "contemplative and questioning",
  "expertise_domains": "ethics, consciousness, meaning",
  "contextual_modifier": "emphasis on deeper implications",
  "cultural_sensitivity": "universal human concerns"
}
```

### Namespace Configurations  
```json
{
  "base_setting": "quantum-realm",
  "core_metaphors": "probability waves, quantum entanglement, observer effects",
  "power_structures": "consciousness nodes, reality stabilizers",
  "technology_level": "thought-responsive quantum manipulation",
  "mapping_rules": "emotions become quantum states, decisions collapse possibilities"
}
```

## 🚀 Deployment Ready

### Local Development
- Use `start_lpe.py` for quick testing
- Full CLI available for development workflows
- Web interface for interactive exploration

### Cloud Deployment
- FastAPI backend ready for containerization
- Database schema supports multi-user environments
- API endpoints ready for Discourse plugin integration
- Stateless design supports horizontal scaling

## 🔮 Future Extensions

The dynamic configuration system supports:
- **Custom Attribute Types**: Create domain-specific attributes
- **Collaborative Configuration**: Multiple users editing shared attributes
- **Version Control**: Track configuration changes over time
- **A/B Testing**: Compare different configuration approaches
- **Machine Learning**: Learn optimal configurations from usage patterns

## 📚 Technical References

- **Dynamic Attributes**: `lamish_projection_engine/config/dynamic_attributes.py`
- **Back-Translation**: `lamish_projection_engine/core/translation_roundtrip.py`
- **Web Interface**: `lamish_projection_engine/web/app.py`
- **Enhanced Models**: `lamish_projection_engine/core/enhanced_models.py`
- **CLI Commands**: `lamish_projection_engine/cli/main.py`

The Lamish Projection Engine has evolved into a sophisticated platform for allegorical narrative transformation with advanced configuration management and semantic analysis capabilities.