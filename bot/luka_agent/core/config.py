"""
luka_agent configuration - minimal settings for standalone operation.

Only includes settings actually used by luka_agent components.
"""
from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Directories
DIR = Path(__file__).absolute().parent.parent.parent
BOT_DIR = Path(__file__).absolute().parent.parent
LOCALES_DIR = f"{BOT_DIR}/locales"
I18N_DOMAIN = "messages"


class EnvBaseSettings(BaseSettings):
    """Base settings with .env file loading."""
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


class RedisSettings(EnvBaseSettings):
    """Redis cache and storage settings."""
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASS: str | None = None
    REDIS_DATABASE: int = 0

    @property
    def redis_url(self) -> str:
        if self.REDIS_PASS:
            return f"redis://{self.REDIS_PASS}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DATABASE}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DATABASE}"


class LLMSettings(EnvBaseSettings):
    """LLM settings for Ollama provider."""
    
    # Ollama Provider Settings
    # IMPORTANT: OLLAMA_URL should be the BASE URL without /v1 suffix
    # Example: http://localhost:11434 (NOT http://localhost:11434/v1)
    OLLAMA_URL: str = "http://localhost:11434"


class ElasticsearchSettings(EnvBaseSettings):
    """Elasticsearch Knowledge Base settings."""
    
    # Connection Settings
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    ELASTICSEARCH_ENABLED: bool = True  # Master switch for KB functionality
    ELASTICSEARCH_TIMEOUT: int = 30  # Request timeout in seconds
    ELASTICSEARCH_VERIFY_CERTS: bool = False  # SSL certificate verification
    
    # Index Settings
    ELASTICSEARCH_USER_KB_PREFIX: str = "tg-kb-user-"  # User KB index pattern
    ELASTICSEARCH_GROUP_KB_PREFIX: str = "tg-kb-group-"  # Group KB index pattern
    ELASTICSEARCH_TOPICS_PREFIX: str = "tg-topics-"  # Topics index pattern
    
    # Embedding Settings
    EMBEDDING_DIMENSIONS: int = 768  # Vector dimensions for embeddings
    
    # Search Settings
    DEFAULT_MIN_SCORE: float = 0.1  # Minimum relevance score for search results
    DEFAULT_MAX_RESULTS: int = 5  # Default number of search results
    
    # Indexing Settings
    INDEX_REFRESH_IMMEDIATE: bool = True  # Refresh index immediately after indexing


class LukaSettings(EnvBaseSettings):
    """Luka agent settings."""
    
    # YouTube Tool Configuration
    YOUTUBE_TRANSCRIPT_ENABLED: bool = True  # Enable YouTube transcript tool


class Settings(
    RedisSettings,
    LLMSettings,
    ElasticsearchSettings,
    LukaSettings,
):
    """Combined settings for luka_agent."""
    pass


# Global settings instance
settings = Settings()
