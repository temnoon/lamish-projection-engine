#!/usr/bin/env python3
"""PostgreSQL database setup with embeddings for LPE."""

import os
import json
import asyncio
import asyncpg
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import numpy as np

# Database configuration
DB_CONFIG = {
    'host': os.getenv('LPE_POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('LPE_POSTGRES_PORT', '5432')),
    'user': os.getenv('LPE_POSTGRES_USER', 'lpe_user'), 
    'password': os.getenv('LPE_POSTGRES_PASSWORD', 'lpe_password'),
    'database': os.getenv('LPE_POSTGRES_DB', 'lamish_projection_engine')
}

@dataclass
class EmbeddedContent:
    id: str
    content_type: str  # 'projection', 'namespace', 'persona', 'question', 'translation'
    title: str
    content: str
    metadata: Dict[str, Any]
    embedding: List[float]
    created_at: datetime

class LPEDatabase:
    def __init__(self):
        self.pool = None
    
    async def initialize(self):
        """Initialize database connection pool and create tables."""
        try:
            self.pool = await asyncpg.create_pool(
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                database=DB_CONFIG['database'],
                min_size=1,
                max_size=10
            )
            
            await self.create_tables()
            print("✅ PostgreSQL database initialized with embeddings support")
            
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            print("Ensure PostgreSQL is running and pgvector extension is available")
            self.pool = None
    
    async def create_tables(self):
        """Create tables with proper schema including vector embeddings."""
        async with self.pool.acquire() as conn:
            # Enable pgvector extension for embeddings
            await conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            
            # Create projections table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS projections (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    job_id UUID,
                    title VARCHAR(255) NOT NULL,
                    original_narrative TEXT NOT NULL,
                    final_projection TEXT NOT NULL,
                    reflection TEXT,
                    persona VARCHAR(100) NOT NULL,
                    namespace VARCHAR(100) NOT NULL,
                    style VARCHAR(100) NOT NULL,
                    input_metadata JSONB,
                    embedding vector(768),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(job_id)
                );
            """)
            
            # Create namespaces table  
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS namespaces (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(100) UNIQUE NOT NULL,
                    description TEXT NOT NULL,
                    generation_prompt TEXT,
                    usage_count INTEGER DEFAULT 0,
                    characteristics JSONB,
                    embedding vector(768),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            
            # Create personas table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS personas (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    name VARCHAR(100) UNIQUE NOT NULL,
                    description TEXT NOT NULL,
                    generation_prompt TEXT,
                    usage_count INTEGER DEFAULT 0,
                    characteristics JSONB,
                    embedding vector(768),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                );
            """)
            
            # Create translations table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS translations (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    job_id UUID,
                    original_text TEXT NOT NULL,
                    intermediate_language VARCHAR(50) NOT NULL,
                    forward_translation TEXT NOT NULL,
                    back_translation TEXT NOT NULL,
                    analysis TEXT,
                    semantic_drift FLOAT,
                    metadata JSONB,
                    embedding vector(768),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(job_id)
                );
            """)
            
            # Create maieutic_sessions table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS maieutic_sessions (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    job_id UUID,
                    narrative TEXT NOT NULL,
                    goal VARCHAR(50) NOT NULL,
                    questions JSONB NOT NULL,
                    metadata JSONB,
                    embedding vector(768),
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    UNIQUE(job_id)
                );
            """)
            
            # Create vector similarity indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS projections_embedding_idx ON projections USING ivfflat (embedding vector_cosine_ops);")
            await conn.execute("CREATE INDEX IF NOT EXISTS namespaces_embedding_idx ON namespaces USING ivfflat (embedding vector_cosine_ops);")
            await conn.execute("CREATE INDEX IF NOT EXISTS personas_embedding_idx ON personas USING ivfflat (embedding vector_cosine_ops);")
            await conn.execute("CREATE INDEX IF NOT EXISTS translations_embedding_idx ON translations USING ivfflat (embedding vector_cosine_ops);")
            await conn.execute("CREATE INDEX IF NOT EXISTS maieutic_embedding_idx ON maieutic_sessions USING ivfflat (embedding vector_cosine_ops);")
            
            print("✅ Database tables created with vector indexes")
    
    async def store_projection(self, job_id: str, projection_data: Dict[str, Any], embedding: List[float]):
        """Store a projection with its embedding."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO projections 
                (job_id, title, original_narrative, final_projection, reflection, 
                 persona, namespace, style, input_metadata, embedding)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (job_id) DO UPDATE SET
                    final_projection = EXCLUDED.final_projection,
                    reflection = EXCLUDED.reflection,
                    embedding = EXCLUDED.embedding
            """, 
                job_id,
                f"Projection: {projection_data.get('persona', '')} in {projection_data.get('namespace', '')}",
                projection_data.get('narrative', ''),
                projection_data.get('final_projection', ''),
                projection_data.get('reflection', ''),
                projection_data.get('persona', ''),
                projection_data.get('namespace', ''),
                projection_data.get('style', ''),
                json.dumps(projection_data),
                embedding
            )
    
    async def store_namespace(self, name: str, description: str, prompt: str, embedding: List[float]):
        """Store a generated namespace with its embedding."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO namespaces (name, description, generation_prompt, embedding)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (name) DO UPDATE SET
                    description = EXCLUDED.description,
                    generation_prompt = EXCLUDED.generation_prompt,
                    embedding = EXCLUDED.embedding
            """, name, description, prompt, embedding)
    
    async def store_persona(self, name: str, description: str, prompt: str, embedding: List[float]):
        """Store a generated persona with its embedding."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO personas (name, description, generation_prompt, embedding)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (name) DO UPDATE SET
                    description = EXCLUDED.description,
                    generation_prompt = EXCLUDED.generation_prompt,
                    embedding = EXCLUDED.embedding
            """, name, description, prompt, embedding)
    
    async def store_translation(self, job_id: str, translation_data: Dict[str, Any], embedding: List[float]):
        """Store a translation analysis with its embedding."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO translations 
                (job_id, original_text, intermediate_language, forward_translation,
                 back_translation, analysis, semantic_drift, metadata, embedding)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                ON CONFLICT (job_id) DO UPDATE SET
                    forward_translation = EXCLUDED.forward_translation,
                    back_translation = EXCLUDED.back_translation,
                    analysis = EXCLUDED.analysis,
                    embedding = EXCLUDED.embedding
            """,
                job_id,
                translation_data.get('original_text', ''),
                translation_data.get('intermediate_language', ''),
                translation_data.get('intermediate_text', ''),
                translation_data.get('final_text', ''),
                translation_data.get('analysis', ''),
                translation_data.get('semantic_drift', 0.0),
                json.dumps(translation_data),
                embedding
            )
    
    async def store_maieutic_session(self, job_id: str, maieutic_data: Dict[str, Any], embedding: List[float]):
        """Store a maieutic dialogue session with its embedding."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO maieutic_sessions 
                (job_id, narrative, goal, questions, metadata, embedding)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (job_id) DO UPDATE SET
                    questions = EXCLUDED.questions,
                    metadata = EXCLUDED.metadata,
                    embedding = EXCLUDED.embedding
            """,
                job_id,
                maieutic_data.get('narrative', ''),
                maieutic_data.get('goal', ''),
                json.dumps(maieutic_data.get('questions', [])),
                json.dumps(maieutic_data),
                embedding
            )
    
    async def find_similar_projections(self, embedding: List[float], limit: int = 5) -> List[Dict]:
        """Find similar projections using vector similarity."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, title, original_narrative, final_projection, persona, namespace,
                       embedding <=> $1 as similarity
                FROM projections
                ORDER BY embedding <=> $1
                LIMIT $2
            """, embedding, limit)
            
            return [dict(row) for row in rows]
    
    async def find_similar_namespaces(self, embedding: List[float], limit: int = 5) -> List[Dict]:
        """Find similar namespaces using vector similarity."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT name, description, usage_count,
                       embedding <=> $1 as similarity
                FROM namespaces
                ORDER BY embedding <=> $1
                LIMIT $2
            """, embedding, limit)
            
            return [dict(row) for row in rows]
    
    async def find_similar_personas(self, embedding: List[float], limit: int = 5) -> List[Dict]:
        """Find similar personas using vector similarity."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT name, description, usage_count,
                       embedding <=> $1 as similarity
                FROM personas
                ORDER BY embedding <=> $1
                LIMIT $2
            """, embedding, limit)
            
            return [dict(row) for row in rows]
    
    async def increment_usage(self, table: str, name: str):
        """Increment usage count for namespace or persona."""
        async with self.pool.acquire() as conn:
            await conn.execute(f"""
                UPDATE {table} SET usage_count = usage_count + 1 
                WHERE name = $1
            """, name)
    
    async def get_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        async with self.pool.acquire() as conn:
            stats = {}
            
            for table in ['projections', 'namespaces', 'personas', 'translations', 'maieutic_sessions']:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                stats[table] = count
            
            return stats
    
    async def close(self):
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()

# Global database instance
db = LPEDatabase()

async def initialize_database():
    """Initialize the database - call this on startup."""
    await db.initialize()

async def test_database():
    """Test database connection and basic operations."""
    print("Testing PostgreSQL connection with embeddings...")
    
    await initialize_database()
    
    if db.pool:
        # Test storing a sample projection
        sample_embedding = np.random.rand(768).tolist()
        
        await db.store_projection(
            "test-job-123",
            {
                "narrative": "A test narrative",
                "final_projection": "A test projection",
                "reflection": "A test reflection",
                "persona": "philosopher",
                "namespace": "lamish-galaxy",
                "style": "academic"
            },
            sample_embedding
        )
        
        # Test similarity search
        similar = await db.find_similar_projections(sample_embedding, 3)
        print(f"Found {len(similar)} similar projections")
        
        # Get stats
        stats = await db.get_stats()
        print(f"Database stats: {stats}")
        
        await db.close()
        print("✅ Database test completed")
    else:
        print("❌ Database connection failed")

if __name__ == "__main__":
    asyncio.run(test_database())