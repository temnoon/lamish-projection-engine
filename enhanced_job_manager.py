#!/usr/bin/env python3
"""Enhanced job manager with PostgreSQL and embeddings support."""

import os
import sys
import json
import uuid
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pathlib import Path

# Add to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from database_setup import db, initialize_database
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

# Fallback to simple SQLite job manager
import sqlite3
from enum import Enum

class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"

class JobType(Enum):
    PROJECTION = "projection"
    TRANSLATION = "translation"
    MAIEUTIC = "maieutic"

class EnhancedJobManager:
    """Job manager with PostgreSQL embeddings support and SQLite fallback."""
    
    def __init__(self, db_path: Optional[str] = None):
        self.use_postgres = POSTGRES_AVAILABLE and os.getenv('LPE_USE_POSTGRES', 'false').lower() == 'true'
        
        # SQLite fallback setup
        self.db_path = db_path or str(Path.home() / ".lpe" / "jobs.db")
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_sqlite_database()
        
        # Initialize embedding model
        self.embedding_model = None
        self._init_embedding_model()
        
        print(f"Enhanced Job Manager initialized (PostgreSQL: {self.use_postgres})")
    
    def _init_sqlite_database(self):
        """Initialize SQLite fallback database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY, type TEXT NOT NULL, status TEXT NOT NULL,
                    title TEXT NOT NULL, description TEXT, input_data TEXT,
                    result_data TEXT, error_message TEXT, progress TEXT,
                    created_at TEXT NOT NULL, started_at TEXT, completed_at TEXT
                )
            """)
            conn.commit()
    
    def _init_embedding_model(self):
        """Initialize embedding model (Ollama or mock)."""
        try:
            import urllib.request
            import simple_config
            
            config = simple_config.SimpleConfig()
            self.ollama_host = config.ollama_host
            self.embedding_model_name = config.embedding_model
            
            # Test embedding model availability
            url = f"{self.ollama_host}/api/tags"
            response = urllib.request.urlopen(url, timeout=5)
            data = json.loads(response.read().decode())
            models = [m.get('name', '') for m in data.get('models', [])]
            
            if self.embedding_model_name in models:
                self.embedding_available = True
                print(f"✅ Embedding model {self.embedding_model_name} available")
            else:
                self.embedding_available = False
                print(f"⚠ Embedding model {self.embedding_model_name} not found")
                
        except Exception as e:
            print(f"Embedding model initialization failed: {e}")
            self.embedding_available = False
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text using Ollama or return None."""
        if not self.embedding_available:
            return None
        
        try:
            import urllib.request
            
            url = f"{self.ollama_host}/api/embeddings"
            data = {
                "model": self.embedding_model_name,
                "prompt": text
            }
            
            json_data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(url, data=json_data)
            req.add_header('Content-Type', 'application/json')
            
            response = urllib.request.urlopen(req, timeout=30)
            result = json.loads(response.read().decode())
            
            return result.get('embedding', [])
            
        except Exception as e:
            print(f"Embedding generation failed: {e}")
            return None
    
    async def store_projection_enhanced(self, job_id: str, input_data: Dict[str, Any], result_data: Dict[str, Any]):
        """Store projection with embeddings if available."""
        # Generate embedding for the projection content
        content_for_embedding = f"{result_data.get('final_projection', '')} {result_data.get('reflection', '')}"
        embedding = self.generate_embedding(content_for_embedding)
        
        if self.use_postgres and embedding:
            try:
                await db.store_projection(job_id, {**input_data, **result_data}, embedding)
                
                # Also increment usage counts for namespace/persona
                await db.increment_usage('namespaces', result_data.get('namespace', ''))
                await db.increment_usage('personas', result_data.get('persona', ''))
                
                print(f"✅ Projection {job_id} stored in PostgreSQL with embedding")
                return
            except Exception as e:
                print(f"PostgreSQL storage failed, falling back to SQLite: {e}")
        
        # Fallback to SQLite storage
        self._store_job_sqlite(job_id, JobType.PROJECTION, input_data, result_data)
    
    async def store_translation_enhanced(self, job_id: str, input_data: Dict[str, Any], result_data: Dict[str, Any]):
        """Store translation analysis with embeddings if available."""
        # Generate embedding for the translation content
        content_for_embedding = f"{result_data.get('original_text', '')} {result_data.get('analysis', '')}"
        embedding = self.generate_embedding(content_for_embedding)
        
        if self.use_postgres and embedding:
            try:
                await db.store_translation(job_id, {**input_data, **result_data}, embedding)
                print(f"✅ Translation {job_id} stored in PostgreSQL with embedding")
                return
            except Exception as e:
                print(f"PostgreSQL storage failed, falling back to SQLite: {e}")
        
        # Fallback to SQLite storage
        self._store_job_sqlite(job_id, JobType.TRANSLATION, input_data, result_data)
    
    async def store_maieutic_enhanced(self, job_id: str, input_data: Dict[str, Any], result_data: Dict[str, Any]):
        """Store maieutic session with embeddings if available."""
        # Generate embedding for the questions content
        questions_text = " ".join(result_data.get('questions', []))
        content_for_embedding = f"{input_data.get('narrative', '')} {questions_text}"
        embedding = self.generate_embedding(content_for_embedding)
        
        if self.use_postgres and embedding:
            try:
                await db.store_maieutic_session(job_id, {**input_data, **result_data}, embedding)
                print(f"✅ Maieutic session {job_id} stored in PostgreSQL with embedding")
                return
            except Exception as e:
                print(f"PostgreSQL storage failed, falling back to SQLite: {e}")
        
        # Fallback to SQLite storage
        self._store_job_sqlite(job_id, JobType.MAIEUTIC, input_data, result_data)
    
    async def store_generated_namespace(self, name: str, description: str, prompt: str):
        """Store generated namespace with embedding."""
        embedding = self.generate_embedding(f"{name} {description}")
        
        if self.use_postgres and embedding:
            try:
                await db.store_namespace(name, description, prompt, embedding)
                print(f"✅ Namespace '{name}' stored with embedding")
            except Exception as e:
                print(f"Failed to store namespace: {e}")
    
    async def store_generated_persona(self, name: str, description: str, prompt: str):
        """Store generated persona with embedding."""
        embedding = self.generate_embedding(f"{name} {description}")
        
        if self.use_postgres and embedding:
            try:
                await db.store_persona(name, description, prompt, embedding)
                print(f"✅ Persona '{name}' stored with embedding")
            except Exception as e:
                print(f"Failed to store persona: {e}")
    
    async def find_similar_content(self, text: str, content_type: str = "projections", limit: int = 5) -> List[Dict]:
        """Find similar content using embeddings."""
        if not self.use_postgres:
            return []
        
        embedding = self.generate_embedding(text)
        if not embedding:
            return []
        
        try:
            if content_type == "projections":
                return await db.find_similar_projections(embedding, limit)
            elif content_type == "namespaces":
                return await db.find_similar_namespaces(embedding, limit)
            elif content_type == "personas":
                return await db.find_similar_personas(embedding, limit)
            else:
                return []
        except Exception as e:
            print(f"Similarity search failed: {e}")
            return []
    
    def _store_job_sqlite(self, job_id: str, job_type: JobType, input_data: Dict[str, Any], result_data: Dict[str, Any]):
        """Store job in SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO jobs 
                (id, type, status, title, description, input_data, result_data, 
                 error_message, progress, created_at, started_at, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id, job_type.value, JobStatus.COMPLETED.value,
                f"{job_type.value.title()} Job",
                f"Processed: {input_data.get('narrative', input_data.get('text', ''))[:50]}...",
                json.dumps(input_data), json.dumps(result_data),
                None, None,
                datetime.now(timezone.utc).isoformat(),
                datetime.now(timezone.utc).isoformat(),
                datetime.now(timezone.utc).isoformat()
            ))
            conn.commit()
    
    def create_and_complete_job_sync(self, job_type: JobType, title: str, input_data: Dict, result_data: Dict) -> str:
        """Synchronous wrapper for job creation and storage."""
        job_id = str(uuid.uuid4())
        
        # Store in SQLite immediately for compatibility
        self._store_job_sqlite(job_id, job_type, input_data, result_data)
        
        # Store with embeddings asynchronously if available
        if self.use_postgres:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Create a new thread for async operations if we're in an async context
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        if job_type == JobType.PROJECTION:
                            executor.submit(asyncio.run, self.store_projection_enhanced(job_id, input_data, result_data))
                        elif job_type == JobType.TRANSLATION:
                            executor.submit(asyncio.run, self.store_translation_enhanced(job_id, input_data, result_data))
                        elif job_type == JobType.MAIEUTIC:
                            executor.submit(asyncio.run, self.store_maieutic_enhanced(job_id, input_data, result_data))
                else:
                    # We can run async directly
                    if job_type == JobType.PROJECTION:
                        asyncio.run(self.store_projection_enhanced(job_id, input_data, result_data))
                    elif job_type == JobType.TRANSLATION:
                        asyncio.run(self.store_translation_enhanced(job_id, input_data, result_data))
                    elif job_type == JobType.MAIEUTIC:
                        asyncio.run(self.store_maieutic_enhanced(job_id, input_data, result_data))
            except Exception as e:
                print(f"Async storage failed: {e}")
        
        return job_id
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics."""
        stats = {"sqlite_available": True}
        
        # SQLite stats
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM jobs")
                stats["sqlite_jobs"] = cursor.fetchone()[0]
        except Exception as e:
            stats["sqlite_error"] = str(e)
        
        # PostgreSQL stats
        if self.use_postgres:
            try:
                pg_stats = await db.get_stats()
                stats.update(pg_stats)
                stats["postgres_available"] = True
            except Exception as e:
                stats["postgres_error"] = str(e)
                stats["postgres_available"] = False
        else:
            stats["postgres_available"] = False
        
        # Embedding stats
        stats["embedding_available"] = self.embedding_available
        stats["embedding_model"] = self.embedding_model_name if hasattr(self, 'embedding_model_name') else None
        
        return stats

# Initialize enhanced job manager
enhanced_job_manager = EnhancedJobManager()

async def initialize_enhanced_database():
    """Initialize PostgreSQL database if available."""
    if enhanced_job_manager.use_postgres:
        await initialize_database()

if __name__ == "__main__":
    async def test_enhanced_manager():
        print("Testing Enhanced Job Manager...")
        
        if enhanced_job_manager.use_postgres:
            await initialize_enhanced_database()
        
        # Test storing a projection
        job_id = enhanced_job_manager.create_and_complete_job_sync(
            JobType.PROJECTION,
            "Test Projection",
            {"narrative": "A test story", "persona": "philosopher", "namespace": "test-realm"},
            {"final_projection": "A transformed story", "reflection": "Deep insights"}
        )
        
        print(f"Created job: {job_id}")
        
        # Get stats
        stats = await enhanced_job_manager.get_database_stats()
        print(f"Database stats: {json.dumps(stats, indent=2)}")
    
    asyncio.run(test_enhanced_manager())