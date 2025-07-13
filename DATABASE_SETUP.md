# LPE Database Setup

The Lamish Projection Engine supports two database backends:

## Current Status: SQLite (Default)
- ✅ **Working**: SQLite with job tracking and history
- ✅ **Storage**: All generations are saved with metadata
- ✅ **Compatibility**: Works out of the box, no setup required

## Optional: PostgreSQL with Embeddings
- 🚧 **Enhanced Features**: Vector embeddings for semantic search
- 🚧 **Advanced Analytics**: Similarity search across generations
- 🚧 **Indexing**: Full-text search and vector similarity

### Quick Setup for PostgreSQL

```bash
# Run the automated setup script
./setup_postgres.sh

# OR manual setup:
brew install postgresql
createdb lamish_projection_engine
pip3 install --user asyncpg psycopg2-binary
```

### Environment Variables

Set these to enable PostgreSQL:

```bash
export LPE_USE_POSTGRES=true
export LPE_POSTGRES_USER=lpe_user
export LPE_POSTGRES_PASSWORD=lpe_password
export LPE_POSTGRES_DB=lamish_projection_engine
```

### Database Schema

When PostgreSQL is enabled, the system creates these tables:

- **projections**: Allegorical transformations with embeddings
- **namespaces**: Generated universe descriptions with embeddings  
- **personas**: Generated character voices with embeddings
- **translations**: Round-trip translation analyses with embeddings
- **maieutic_sessions**: Socratic dialogue sessions with embeddings

### Embedding Model

The system uses Ollama's `nomic-embed-text:latest` for generating embeddings.

Install it with:
```bash
ollama pull nomic-embed-text
```

### Features with PostgreSQL + Embeddings

1. **Semantic Search**: Find similar projections, namespaces, or personas
2. **Usage Analytics**: Track which namespaces/personas are most used
3. **Content Discovery**: Explore related content through vector similarity
4. **Advanced Indexing**: Full-text and vector search capabilities

### Current Implementation

- **SQLite**: ✅ Fully working - stores all job history and results
- **PostgreSQL**: 🚧 Schema ready, needs pgvector extension
- **Embeddings**: 🚧 Code ready, needs embedding model setup
- **Similarity Search**: 🚧 Endpoints ready, needs PostgreSQL setup

### Testing Database

```bash
# Test SQLite (default)
python3 enhanced_job_manager.py

# Test PostgreSQL (if configured)
python3 database_setup.py
```

The system gracefully falls back to SQLite if PostgreSQL is not available, ensuring the interface always works.