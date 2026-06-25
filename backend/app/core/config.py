"""
Application configuration with Pydantic settings validation.
Centralizes environment variable management with type safety.
"""
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List, Optional
import os


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Validates all required configuration on startup.
    """
    
    # =============================================================================
    # APPLICATION SETTINGS
    # =============================================================================
    APP_NAME: str = Field(default="NYX Decision Intelligence API")
    APP_VERSION: str = Field(default="2.1.0")
    DEBUG: bool = Field(default=False)
    ENVIRONMENT: str = Field(default="development")
    
    # =============================================================================
    # SERVER SETTINGS
    # =============================================================================
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    
    # =============================================================================
    # CORS SETTINGS
    # =============================================================================
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000"],
        description="Comma-separated list of allowed origins"
    )
    ALLOW_WILDCARD_CORS: bool = Field(
        default=False,
        description="Allow wildcard CORS (DANGEROUS in production)"
    )
    
    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse comma-separated CORS origins string into list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    # =============================================================================
    # DATABASE SETTINGS
    # =============================================================================
    DATABASE_URL: str = Field(
        default="sqlite:///./nyx.db",
        description="Database connection URL"
    )
    DB_POOL_SIZE: int = Field(default=10, ge=5, le=50)
    DB_MAX_OVERFLOW: int = Field(default=20, ge=10, le=50)
    
    # =============================================================================
    # LLM PROVIDER SETTINGS
    # =============================================================================
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    ANTHROPIC_API_KEY: Optional[str] = Field(default=None)
    GOOGLE_API_KEY: Optional[str] = Field(default=None)
    AZURE_OPENAI_KEY: Optional[str] = Field(default=None)
    AZURE_OPENAI_ENDPOINT: Optional[str] = Field(default=None)
    
    # =============================================================================
    # CACHE SETTINGS (Redis)
    # =============================================================================
    REDIS_URL: Optional[str] = Field(
        default=None,
        description="Redis URL for distributed caching"
    )
    CACHE_TTL: int = Field(default=3600, ge=60, le=86400)  # 1 hour default
    
    # =============================================================================
    # SECURITY SETTINGS
    # =============================================================================
    API_KEY_SECRET: Optional[str] = Field(
        default=None,
        description="Secret key for API authentication"
    )
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_EXPIRATION_MINUTES: int = Field(default=60, ge=5, le=1440)
    
    # =============================================================================
    # RATE LIMITING
    # =============================================================================
    RATE_LIMIT_REQUESTS: int = Field(default=100, ge=10, le=1000)
    RATE_LIMIT_WINDOW: int = Field(default=60, ge=10, le=3600)  # seconds
    
    # =============================================================================
    # LOGGING SETTINGS
    # =============================================================================
    LOG_LEVEL: str = Field(default="INFO")
    LOG_FORMAT: str = Field(default="json")  # "json" or "text"
    
    # =============================================================================
    # MONITORING SETTINGS
    # =============================================================================
    ENABLE_METRICS: bool = Field(default=True)
    METRICS_PORT: int = Field(default=9090)
    
    # =============================================================================
    # VALIDATION METHODS
    # =============================================================================
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def has_llm_keys(self) -> bool:
        """Check if at least one LLM provider is configured."""
        return any([
            self.OPENAI_API_KEY,
            self.ANTHROPIC_API_KEY,
            self.GOOGLE_API_KEY,
            self.AZURE_OPENAI_KEY
        ])
    
    @field_validator('ENVIRONMENT')
    @classmethod
    def validate_environment(cls, v):
        """Validate environment value."""
        allowed = ["development", "staging", "production", "testing"]
        if v.lower() not in allowed:
            raise ValueError(f"Environment must be one of: {allowed}")
        return v.lower()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Dependency for FastAPI endpoints."""
    return settings
