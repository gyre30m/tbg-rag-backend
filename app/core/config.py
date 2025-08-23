"""
Configuration settings for the TBG RAG backend.
Uses Pydantic settings for environment variable management.
"""

from typing import List, Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Supabase Configuration (modern approach)
    supabase_url: str
    supabase_publishable_key: str
    supabase_secret_key: str
    supabase_pat_token: Optional[str] = None  # Personal Access Token for CLI/MCP
    railway_token: Optional[str] = None  # Railway deployment token

    # JWT Configuration (ES256 with JWK)
    supabase_jwt_public_key: Optional[str] = None  # Legacy, not used with JWK
    supabase_jwt_private_key: Optional[str] = None  # Not needed for verification
    jwt_algorithm: str = "ES256"
    supabase_jwks_uri: str = (
        "https://leozlogjxlzsnoijodez.supabase.co/auth/v1/.well-known/jwks.json"
    )

    # Legacy database URL (optional, not used with Supabase)
    database_url: Optional[str] = None

    # AI Services
    openai_api_key: str
    anthropic_api_key: str

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # File Processing Limits
    max_file_size: int = 52428800  # 50MB
    max_files_per_batch: int = 50
    supported_mime_types: str = "application/pdf,text/plain,text/markdown,application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    # Processing Configuration
    chunk_size: int = 1000
    chunk_overlap: int = 200
    embedding_model: str = "text-embedding-3-small"
    max_retries: int = 3

    # Development
    debug: bool = False
    log_level: str = "INFO"
    codecov_token: Optional[str] = None  # For coverage reporting

    @property
    def supported_mime_types_list(self) -> List[str]:
        """Get supported MIME types as a list."""
        return [mime.strip() for mime in self.supported_mime_types.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
