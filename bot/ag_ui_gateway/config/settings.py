"""
Configuration Settings

Pydantic BaseSettings for loading configuration from environment variables.
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Bot Configuration
    BOT_TOKEN: str
    AUTHJWT_SECRET_KEY: str  # Renamed from JWT_SECRET to match luka_bot naming
    
    # Database Configuration
    # PostgreSQL is optional - currently not used (reserved for future features)
    POSTGRES_ENABLED: bool = False  # Set to True if you need it
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "luka"
    POSTGRES_PASSWORD: str = ""  # Optional, only needed if POSTGRES_ENABLED=True
    POSTGRES_DB: str = "luka_bot"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_ECHO: bool = False  # Log all SQL queries
    
    @property
    def DATABASE_URL(self) -> str:
        """PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    # Redis Configuration
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASS: str | None = None  # Match luka_bot naming
    REDIS_DATABASE: int = 0  # Match luka_bot naming
    
    @property
    def REDIS_URL(self) -> str:
        """Redis connection URL."""
        password_part = f":{self.REDIS_PASS}@" if self.REDIS_PASS else ""
        return f"redis://{password_part}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DATABASE}"
    
    # Elasticsearch Configuration
    ELASTICSEARCH_ENABLED: bool = True
    ELASTICSEARCH_URL: str = "http://localhost:9200"  # Use localhost for dev, elasticsearch for Docker
    ELASTICSEARCH_TIMEOUT: int = 30
    ELASTICSEARCH_VERIFY_CERTS: bool = False
    
    # Legacy ES config for backward compatibility
    ES_HOST: str = "elasticsearch"
    ES_PORT: int = 9200
    ES_SCHEME: str = "http"
    
    @property
    def ES_URL(self) -> str:
        """Elasticsearch connection URL (legacy)."""
        return f"{self.ES_SCHEME}://{self.ES_HOST}:{self.ES_PORT}"
    
    # Camunda Configuration
    CAMUNDA_URL: str = "http://camunda:8080/engine-rest"
    
    # Flow API Configuration
    FLOW_API_URL: str
    FLOW_API_SYS_KEY: str = ""
    
    # Warehouse WebSocket Configuration
    WAREHOUSE_WS_URL: str
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "https://t.me"]
    
    # Authentication
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_SECONDS: int = 3600  # 1 hour
    GUEST_TOKEN_EXPIRY_SECONDS: int = 3600  # 1 hour
    
    # Rate Limiting
    GUEST_RATE_LIMIT_PER_MINUTE: int = 20
    AUTH_RATE_LIMIT_PER_MINUTE: int = 60
    GUEST_TOTAL_MESSAGES: int = 20
    
    # File Upload
    MAX_FILE_SIZE_MB: int = 20
    ALLOWED_FILE_TYPES: List[str] = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/gif",
        "text/plain",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ]
    
    # S3/R2 Configuration (from luka_bot)
    S3_ENDPOINT_URL: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_BUCKET_NAME: str = ""
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "text"


# Global settings instance
settings = Settings()

