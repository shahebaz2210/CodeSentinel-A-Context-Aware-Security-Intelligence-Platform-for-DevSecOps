"""Core configuration and settings for CodeSentinel backend."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "CodeSentinel"
    APP_ENV: str = "development"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production-use-random-32-chars"

    # Database
    DATABASE_URL: str = "postgresql://codesentinel:codesentinel@localhost:5432/codesentinel"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Qdrant
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION_NAME: str = "security_knowledge"
    QDRANT_VECTOR_SIZE: int = 768  # Google text-embedding-004 dimension

    # GitHub OAuth App
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_WEBHOOK_SECRET: str = ""
    GITHUB_APP_ID: Optional[str] = None
    GITHUB_APP_PRIVATE_KEY: Optional[str] = None
    GITHUB_CALLBACK_URL: str = "http://localhost:8000/auth/github/callback"

    # LLM Provider (configurable)
    # Google Gemini (free tier via AI Studio)
    GOOGLE_API_KEY: str = ""
    LLM_MODEL: str = "gemini-1.5-flash"        # free-tier Gemini model
    LLM_TEMPERATURE: float = 0.1
    EMBEDDING_MODEL: str = "models/text-embedding-004"  # Google embedding model

    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Risk Engine Weights (deterministic, configurable)
    RISK_WEIGHT_SEVERITY: float = 0.30
    RISK_WEIGHT_EXPLOITABILITY: float = 0.25
    RISK_WEIGHT_CONFIDENCE: float = 0.15
    RISK_WEIGHT_EXPOSURE: float = 0.15
    RISK_WEIGHT_BUSINESS_IMPACT: float = 0.15

    # Security Policy Gate Defaults
    POLICY_BLOCK_ON_CRITICAL: bool = True
    POLICY_BLOCK_ON_EXPOSED_SECRET: bool = True
    POLICY_RISK_SCORE_WARNING_THRESHOLD: float = 60.0
    POLICY_RISK_SCORE_BLOCK_THRESHOLD: float = 80.0

    # Scanning
    SCAN_TIMEOUT_SECONDS: int = 600
    CLONE_TIMEOUT_SECONDS: int = 120
    PATCH_VALIDATION_TIMEOUT_SECONDS: int = 300

    # Knowledge Base
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 64
    RAG_TOP_K: int = 5


@lru_cache()
def get_settings() -> Settings:
    """Return cached Settings instance."""
    return Settings()


settings = get_settings()
