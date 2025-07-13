"""Configuration management for Lamish Projection Engine."""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv


class Settings(BaseSettings):
    """Application settings."""
    
    # Database settings
    postgres_user: str = "lpe_user"
    postgres_password: str = "lpe_password"
    postgres_db: str = "lamish_projection_engine"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    
    # Application settings
    app_name: str = "Lamish Projection Engine"
    debug: bool = False
    log_level: str = "INFO"
    
    # Visualization settings
    default_figure_size: tuple = (10, 8)
    default_dpi: int = 100
    color_palette: str = "viridis"
    
    # Processing settings
    batch_size: int = 1000
    max_workers: int = 4
    cache_dir: Path = Path.home() / ".lpe_cache"
    
    # LLM settings
    ollama_host: str = "http://localhost:11434"
    llm_model: str = "gemma3:12b"  # Default model, overridden by env
    embedding_model: str = "nomic-embed-text:latest"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 8192
    use_mock_llm: bool = False  # Set to True to use mock transformer for testing
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_prefix="LPE_"
    )
    
    @field_validator("cache_dir", mode="before")
    @classmethod
    def create_cache_dir(cls, v):
        """Ensure cache directory exists."""
        cache_path = Path(v)
        cache_path.mkdir(parents=True, exist_ok=True)
        return cache_path
    
    @property
    def database_url(self) -> str:
        """Construct database URL."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


def load_config(env_file: Optional[Path] = None) -> Settings:
    """Load configuration from environment and .env file."""
    if env_file is None:
        env_file = Path.cwd() / ".env"
    
    if env_file.exists():
        load_dotenv(env_file)
    
    return Settings()


def get_config() -> Settings:
    """Get cached configuration instance."""
    if not hasattr(get_config, "_instance"):
        get_config._instance = load_config()
    return get_config._instance


def reload_config() -> Settings:
    """Force reload configuration from environment."""
    get_config._instance = load_config()
    return get_config._instance