# Lamish Projection Engine - Quick Start

## Setup

### Option 1: Using venv (Recommended)

1. **Start the database:**
   ```bash
   docker-compose up -d
   ```

2. **Run the setup script:**
   ```bash
   ./setup.sh
   ```
   
   This will:
   - Create a Python virtual environment
   - Install all dependencies
   - Initialize the database

3. **Activate the environment:**
   ```bash
   source venv/bin/activate
   ```

### Option 2: Using Conda

1. **Start the database:**
   ```bash
   docker-compose up -d
   ```

2. **Create and activate conda environment:**
   ```bash
   conda env create -f environment.yml
   conda activate lpe
   ```

3. **Initialize the database:**
   ```bash
   python scripts/init_db.py
   ```

### Option 3: Manual Setup

1. **Start the database:**
   ```bash
   docker-compose up -d
   ```

2. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Initialize the database:**
   ```bash
   python scripts/init_db.py
   ```

## Using the CLI

### Check system status:
```bash
python -m lamish_projection_engine.cli.main status
```

### List available agents:
```bash
python -m lamish_projection_engine.cli.main list-agents
```

### Project a narrative:
```bash
# Interactive mode (enter text when prompted)
python -m lamish_projection_engine.cli.main project --show-steps

# From text
python -m lamish_projection_engine.cli.main project -t "Your narrative here" --show-steps

# From file
python -m lamish_projection_engine.cli.main project -f story.txt -p philosopher -n lamish-galaxy -s poetic --show-steps
```

### Explore projections:
```bash
# List recent
python -m lamish_projection_engine.cli.main explore

# View specific projection
python -m lamish_projection_engine.cli.main explore -p 1

# Search projections
python -m lamish_projection_engine.cli.main explore -s "conflict"
```

## Run the Demo

```bash
python demo.py
```

This will walk you through creating projections with different personas, namespaces, and styles.

## Maieutic (Socratic) Dialogue with Projection

Explore your narratives through guided questioning, then create an informed allegorical projection:

### Run the maieutic dialogue:
```bash
# Interactive mode (includes projection offer)
python maieutic.py

# Or through CLI
python -m lamish_projection_engine.cli.main maieutic

# With a file
python -m lamish_projection_engine.cli.main maieutic -f story.txt -m 7

# Skip projection after dialogue
python -m lamish_projection_engine.cli.main maieutic --no-project

# Demo with examples
python demo_maieutic.py
```

### How it works:
1. **Questioning Phase**: The system asks thoughtful questions to explore your narrative
2. **Insight Extraction**: Key discoveries are identified from your answers
3. **Configuration Suggestion**: Based on insights, appropriate persona/namespace/style are suggested
4. **Informed Projection**: The narrative is projected using both the original text and discovered insights

The maieutic method helps you discover deeper insights through questions, which then inform a more meaningful allegorical transformation.

## Available Configurations

### Personas:
- `neutral` - Balanced observer
- `advocate` - Emphasizes positives  
- `critic` - Analytical questioning
- `philosopher` - Seeks deeper meaning
- `storyteller` - Narrative focus

### Namespaces:
- `lamish-galaxy` - Sci-fi allegory space
- `medieval-realm` - Fantasy kingdoms
- `corporate-dystopia` - Business allegories
- `natural-world` - Ecological metaphors
- `quantum-realm` - Abstract probabilities

### Styles:
- `standard` - Clear and accessible
- `academic` - Formal scholarly
- `poetic` - Rich in metaphor
- `technical` - Precise detailed
- `casual` - Conversational