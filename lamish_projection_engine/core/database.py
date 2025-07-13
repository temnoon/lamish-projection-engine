"""Database connection and management for LPE."""
from typing import Optional, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
import logging

from lamish_projection_engine.utils.config import get_config

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self, database_url: Optional[str] = None):
        """Initialize database manager."""
        config = get_config()
        self.database_url = database_url or config.database_url
        self.engine = None
        self.SessionLocal = None
        self._initialize()
    
    def _initialize(self):
        """Initialize database engine and session factory."""
        try:
            self.engine = create_engine(
                self.database_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                echo=False
            )
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            logger.info("Database engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Session:
        """Get database session context manager."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def check_connection(self) -> bool:
        """Check if database connection is working."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                return result.scalar() == 1
        except SQLAlchemyError as e:
            logger.error(f"Database connection check failed: {e}")
            return False
    
    def check_pgvector(self) -> bool:
        """Check if pgvector extension is available."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
                )
                return result.rowcount > 0
        except SQLAlchemyError as e:
            logger.error(f"pgvector check failed: {e}")
            return False


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager() -> DatabaseManager:
    """Get or create database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def check_connection() -> bool:
    """Check database connection status."""
    try:
        db_manager = get_db_manager()
        return db_manager.check_connection() and db_manager.check_pgvector()
    except Exception:
        return False