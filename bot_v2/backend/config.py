"""Configuration management for bot_v2"""
import os
from typing import Optional
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://bot_user:bot_pw@localhost:5432/bot_v2_db"
    )
    
    # API
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    api_prefix: str = "/api/v1"
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "change-me-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # LLM Provider (optional, only for intent resolution)
    llm_provider: Optional[str] = os.getenv("LLM_PROVIDER", None)  # openai, anthropic, etc.
    llm_api_key: Optional[str] = os.getenv("LLM_API_KEY", None)
    llm_model: Optional[str] = os.getenv("LLM_MODEL", "gpt-4o-mini")
    llm_base_url: Optional[str] = os.getenv("LLM_BASE_URL", None)
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # CORS
    cors_origins: list[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:3000,http://localhost:3001"
    ).split(",")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
