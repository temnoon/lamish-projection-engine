# Lamish Projection Engine (LPE)

AI-powered allegorical narrative transformation system with multi-provider LLM support, interactive Socratic dialogue, and secure credential management.

## 🌟 Features

### Core Transformations
- **🎭 Allegorical Projections**: Transform narratives through different personas and fictional universes
- **🔄 Round-trip Translation Analysis**: Analyze semantic drift through intermediate languages
- **🤔 Interactive Maieutic Dialogue**: Socratic questioning with synthesis into revised narratives

### Multi-Provider LLM Support
- **🔐 Secure API Key Storage**: macOS Keychain integration
- **🤖 Multiple Providers**: OpenAI, Anthropic, Google Gemini, Ollama
- **⚡ Automatic Fallback**: Seamless switching between providers
- **🎛️ Configurable**: Per-provider model selection and parameters

### Advanced Features
- **📊 PostgreSQL Integration**: Optional embeddings and semantic search
- **📋 Copy/Save Actions**: Export content as markdown with timestamps
- **🎨 Asset Management**: Custom personas, namespaces, and styles
- **📱 Interactive UI**: Real-time processing with collapsible Q&A

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- macOS (for Keychain integration)
- Ollama (for local models) - optional

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/temnoon/lamish-projection-engine.git
   cd lamish-projection-engine
   ```

2. **Start all services**:
   ```bash
   ./start_lpe.sh
   ```

3. **Access interfaces**:
   - **Main Interface**: http://localhost:8000
   - **Job Admin**: http://localhost:8001  
   - **LLM Admin**: http://localhost:8002

### First Time Setup

1. **Configure LLM Providers** (http://localhost:8002):
   - Add API keys for OpenAI, Anthropic, or Google
   - Keys are stored securely in macOS Keychain
   - Test connections and select models

2. **Try the Examples**:
   - Create an allegorical projection
   - Run a round-trip translation analysis
   - Engage in Maieutic dialogue

## 📱 Usage

### Allegorical Projections
Transform any narrative through different personas and fictional universes:

```
Input: "A team struggles with a difficult project deadline"
Persona: philosopher
Namespace: lamish-galaxy
→ Allegorical projection in the context of cosmic exploration
```

### Maieutic Dialogue
Interactive Socratic questioning to deepen understanding:

1. Enter a narrative to explore
2. Generate thought-provoking questions
3. Answer questions in any order
4. Synthesize insights into a revised narrative

### Round-trip Translation
Analyze semantic drift through intermediate languages:

```
English → Spanish → English
Analyze what meaning was preserved, lost, or gained
```

## 🔧 Configuration

### LLM Providers

Configure in the LLM Admin interface (http://localhost:8002):

- **OpenAI**: GPT-4, GPT-4-turbo, GPT-3.5-turbo
- **Anthropic**: Claude-3 Opus, Sonnet, Haiku
- **Google**: Gemini Pro, Gemini Pro Vision
- **Ollama**: Any local model (llama3.2, gemma3, etc.)

### Database Options

**SQLite (Default)**:
- No setup required
- Stores all job history and results

**PostgreSQL (Optional)**:
- Advanced embeddings and semantic search
- Run `./setup_postgres.sh` for automated setup
- Set `LPE_USE_POSTGRES=true` environment variable

## 🛠️ Architecture

### Services
- **Port 8000**: Main user interface
- **Port 8001**: Job administration and database viewer
- **Port 8002**: Multi-provider LLM configuration

### Key Components
- `immediate_interface.py`: Main web interface with real-time processing
- `multi_llm_admin.py`: Secure multi-provider LLM configuration
- `enhanced_job_manager.py`: Database abstraction with embeddings
- `llm_providers.py`: Unified interface for all LLM providers
- `keychain_manager.py`: macOS Keychain integration

## 🔐 Security

- **API Keys**: Stored in macOS Keychain, never in config files
- **Encryption**: All credentials encrypted at rest
- **No Logging**: API keys never appear in logs or console output
- **Secure Defaults**: Environment variables for sensitive settings

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Built with Claude Code assistance
- Inspired by allegorical thinking and Socratic dialogue
- Uses multiple LLM providers for diverse perspectives

---

**Note**: This is a research and educational tool for exploring narrative transformation through AI. Always review generated content for accuracy and appropriateness.