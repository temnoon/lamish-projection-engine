# Multi-Provider LLM Setup Guide

The LPE now supports multiple LLM providers with secure API key storage in macOS Keychain.

## 🚀 Quick Start

```bash
# Start all LPE services
./start_lpe.sh

# Or restart existing services
./start_lpe.sh --restart
```

## 🔧 Configuration

### Multi-Provider Admin Interface
Visit http://localhost:8002 to configure providers:

- **OpenAI**: GPT-4, GPT-3.5-turbo models
- **Anthropic**: Claude-3 Opus, Sonnet, Haiku
- **Google**: Gemini Pro models
- **Ollama**: Local models (llama3.2, gemma3, etc.)

## 🔐 Secure API Key Storage

API keys are stored in **macOS Keychain**, not in config files:

### Adding API Keys
1. Open http://localhost:8002
2. Enter API key for each provider
3. Keys are encrypted and stored in Keychain
4. Test connection to verify

### Managing Keys
```bash
# View stored keys
python3 -c "from keychain_manager import keychain; print(keychain.list_stored_keys())"

# Test keychain access
python3 keychain_manager.py
```

### Manual Keychain Operations
```bash
# Store key manually
security add-generic-password -s "LamishProjectionEngine" -a "openai_api_key" -w "your-api-key"

# Retrieve key
security find-generic-password -s "LamishProjectionEngine" -a "openai_api_key" -w

# Delete key
security delete-generic-password -s "LamishProjectionEngine" -a "openai_api_key"
```

## 🎯 Provider Configuration

### OpenAI Setup
1. Get API key from https://platform.openai.com/api-keys
2. Add to http://localhost:8002
3. Select model: gpt-4, gpt-4-turbo, gpt-3.5-turbo
4. Configure temperature, max tokens

### Anthropic Setup  
1. Get API key from https://console.anthropic.com/
2. Add to http://localhost:8002
3. Select model: claude-3-opus, claude-3-sonnet, claude-3-haiku
4. Configure parameters

### Google Setup
1. Get API key from https://aistudio.google.com/app/apikey
2. Add to http://localhost:8002
3. Select model: gemini-pro, gemini-pro-vision
4. Configure parameters

### Ollama Setup
1. Install Ollama: `brew install ollama`
2. Pull models: `ollama pull llama3.2:latest`
3. No API key required (local)
4. Auto-detected when running

## 🔄 Usage

### Default Provider
Set in http://localhost:8002 or by editing config:
```json
{
  "default_provider": "openai",
  "provider_settings": {
    "openai": {
      "default_model": "gpt-4",
      "temperature": 0.7,
      "max_tokens": 4096
    }
  }
}
```

### Programmatic Usage
```python
from llm_providers import llm_manager

# Generate with default provider
result = llm_manager.generate_text("Hello world")

# Generate with specific provider
result = llm_manager.generate_text("Hello", provider="openai", model="gpt-4")

# Check availability
providers = llm_manager.get_available_providers()
print(providers)  # {'openai': True, 'anthropic': False, 'google': True, 'ollama': True}
```

## 📊 Service Architecture

### Port Layout
- **8000**: User Interface (projections, translations, maieutic)
- **8001**: Job Admin (SQLite/PostgreSQL management)
- **8002**: Multi-Provider LLM Admin (API keys, models)

### Data Flow
1. User Interface → Enhanced Job Manager → PostgreSQL/SQLite
2. LLM requests → Unified LLM Manager → Provider APIs
3. API keys → macOS Keychain (encrypted)
4. Embeddings → PostgreSQL with pgvector (optional)

## 🔍 Monitoring

### Check Service Status
```bash
# View running services
lsof -i :8000 -i :8001 -i :8002

# Test providers
python3 -c "
from llm_providers import llm_manager
for name, available in llm_manager.get_available_providers().items():
    print(f'{name}: {\"✅\" if available else \"❌\"}')"
```

### Logs and Debugging
- Check console output when starting services
- Provider errors shown in admin interface
- Test connections via admin interface

## 🛠️ Troubleshooting

### Common Issues

**"Provider not available"**
- Check API key in Keychain
- Verify internet connection
- Test in admin interface

**"Keychain access denied"**  
- Grant terminal Keychain access in System Preferences
- Run: `python3 keychain_manager.py` to test

**"Ollama not running"**
- Start Ollama: `ollama serve`
- Check models: `ollama list`

**"Port already in use"**
- Use `./start_lpe.sh --restart`
- Or manually kill: `pkill -f "interface.py"`

### Recovery
```bash
# Reset all configurations
rm ~/.lpe/multi_llm_config.json
rm ~/.lpe/llm_config.json

# Remove keychain entries
security delete-generic-password -s "LamishProjectionEngine" -a "openai_api_key"
security delete-generic-password -s "LamishProjectionEngine" -a "anthropic_api_key"
security delete-generic-password -s "LamishProjectionEngine" -a "google_api_key"
```

## 🔮 Advanced Features

### Automatic Fallback
The system automatically falls back to available providers if the primary fails.

### Cost Optimization
- Use Ollama for development
- Switch to cloud providers for production
- Configure different models per use case

### Custom Models
Each provider supports multiple models with different capabilities and costs.

## 📁 File Structure

```
lpe_dev/
├── keychain_manager.py      # Secure API key storage
├── llm_providers.py         # Unified provider interface  
├── multi_llm_admin.py       # Web admin for providers
├── immediate_interface.py   # Updated with multi-provider
├── enhanced_job_manager.py  # Database with embeddings
├── start_lpe.sh            # Startup script
└── MULTI_PROVIDER_SETUP.md # This guide
```