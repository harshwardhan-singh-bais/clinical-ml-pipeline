"""
Application Settings and Configuration
Phase 1: Application Bootstrap & Environment Setup

Loads and validates all environment variables required for the system.
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file before Settings initialization
load_dotenv()


class Settings(BaseSettings):
    # Dataset paths (for test compatibility)
    STATPEARLS_DATASET_PATH: Optional[str] = None
    MEDCASE_REASONING_PATH: Optional[str] = None
    ASCLEPIUS_NOTES_PATH: Optional[str] = None
    AUGMENTED_NOTES_PATH: Optional[str] = None
    """Application settings loaded from environment variables."""
    
    # Gemini API Configuration
    GEMINI_API_KEY: str
    GEMINI_MODEL: str = "models/gemini-flash-latest"
    
    # Sentence Transformers Configuration (local embeddings)
    SENTENCE_TRANSFORMERS_MODEL: str = "sentence-transformers/all-mpnet-base-v2"
    
    # Hugging Face Configuration
    HUGGINGFACE_TOKEN: Optional[str] = None
    
    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    
    # Database Configuration
    DATABASE_URL: str
    
    # Qdrant Configuration
    QDRANT_URL: Optional[str] = None
    QDRANT_API_KEY: Optional[str] = None

    # Hugging Face Configuration
    HUGGINGFACE_TOKEN: Optional[str] = None
    
    # Application Configuration
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = True
    
    # Model Configuration (StatPearls + Sentence Transformers)
    EMBEDDING_DIMENSION: int = 768  # all-mpnet-base-v2 embedding dimension
    MAX_CHUNK_SIZE: int = 400
    CHUNK_OVERLAP: int = 80
    
    # StatPearls Ingestion Configuration (TEST MODE)
    MAX_STATPEARLS_CHUNKS: int = 2000  # Hard limit for test mode
    MIN_CONTENT_LENGTH: int = 300
    
    # Retrieval Configuration
    TOP_K_RETRIEVAL: int = 25  # Increased for demo/recall
    SIMILARITY_THRESHOLD: float = 0.15  # Lowered for cross-domain retrieval
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    # Derived Properties
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


def validate_environment():
    """
    Validate that all critical environment variables are set.
    If this fails → app must not start (Phase 1 requirement).
    """
    critical_vars = [
        "GEMINI_API_KEY",
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "DATABASE_URL"
    ]
    
    missing = []
    for var in critical_vars:
        if not getattr(settings, var, None):
            missing.append(var)
    
    if missing:
        raise RuntimeError(
            f"Critical environment variables missing: {', '.join(missing)}. "
            "Application cannot start."
        )
    
    return True
