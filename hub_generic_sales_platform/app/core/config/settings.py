"""
Cấu hình toàn hệ thống sử dụng Pydantic Settings
Dựa trên env.example hiện có của dự án
"""
from typing import Optional, Literal
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Cấu hình tổng của ứng dụng"""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # env
    debug: bool = Field(default=False, alias="DEBUG")
    environment: str = Field(default="dev", alias="ENVIRONMENT")

    # app
    app_name: str = Field(default="bot_v4", alias="APP_NAME")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")
    title: str = Field(default="AI Assistant Hub", alias="TITLE")
    description: str = Field(default="AI Hub với Hybrid Orchestration 2026", alias="DESCRIPTION")
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    reload: bool = Field(default=True, alias="RELOAD")

    # CORS
    cors_origins: str = Field(default="*", alias="CORS_ORIGINS")
    
    # JWT Authentication
    jwt_secret_key: str = Field(default="your-secret-key-change-in-production", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=1440, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")  # 24 hours

    # DB
    database_url: str = Field(default="postgresql+asyncpg://postgres:postgres@localhost:5432/bot_hub", alias="DATABASE_URL")
    sync_url: str = Field(default="postgresql://postgres:postgres@localhost:5432/bot_hub", alias="SYNC_URL")
    db_pool_size: int = Field(default=20, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=20, alias="DB_MAX_OVERFLOW")
    db_pool_timeout: int = Field(default=60, alias="DB_POOL_TIMEOUT")
    db_pool_recycle: int = Field(default=1800, alias="DB_POOL_RECYCLE") # 30 minutes
    
    # Redis (for Caching & Idempotency)
    redis_url: Optional[str] = Field(default=None, alias="REDIS_URL")

    # LLM
    llm_timeout: int = Field(default=30, alias="LLM_TIMEOUT")
    llm_temperature: float = Field(default=0.3, alias="LLM_TEMPERATURE")

    ai_provider_primary: str = Field(default="openai", alias="AI_PROVIDER_PRIMARY")
    ai_provider_fallback: str = Field(default="litellm", alias="AI_PROVIDER_FALLBACK")

    litellm_api_base: str = Field(default="", alias="LITELLM_API_BASE")
    litellm_api_key: str = Field(default="", alias="LITELLM_API_KEY")
    litellm_chat_model: str = Field(default="gpt-3.5-turbo", alias="LITELLM_CHAT_MODEL")
    litellm_embedding_model: str = Field(default="text-embedding-3-small", alias="LITELLM_EMBEDDING_MODEL")

    openai_api_base: str = Field(default="https://api.openai.com/v1", alias="OPENAI_API_BASE")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_chat_model: str = Field(default="gpt-4-turbo-preview", alias="OPENAI_CHAT_MODEL")
    openai_embedding_model: str = Field(default="text-embedding-3-small", alias="OPENAI_EMBEDDING_MODEL")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="console", alias="LOG_FORMAT")
    log_file_enabled: bool = Field(default=False, alias="LOG_FILE_ENABLED")
    log_file_path: str = Field(default="logs/app.log", alias="LOG_FILE_PATH")
    log_file_max_bytes: int = Field(default=10485760, alias="LOG_FILE_MAX_BYTES")  # 10MB
    log_file_backup_count: int = Field(default=5, alias="LOG_FILE_BACKUP_COUNT")

    # Orchestration & Tiers
    social_patterns: dict[str, str] = Field(
        default={
            r"^(chào|hi|hello|hey)": "Chào bạn! Tôi có thể giúp gì cho bạn hôm nay?",
            r"^(cám ơn|cảm ơn|thanks|thank you)": "Không có gì! Rất vui được hỗ trợ bạn.",
            r"^(tạm biệt|bye|goodbye)": "Tạm biệt! Hẹn gặp lại bạn lần sau."
        },
        alias="SOCIAL_PATTERNS"
    )
    
    cost_fast_path: float = Field(default=0.0, alias="COST_FAST_PATH")
    cost_knowledge_base: float = Field(default=0.0001, alias="COST_KNOWLEDGE_BASE")
    cost_agentic_base: float = Field(default=0.005, alias="COST_AGENTIC_BASE")
    cost_agentic_per_char: float = Field(default=0.00005, alias="COST_AGENTIC_PER_CHAR")
    
    # Cache Configuration
    semantic_cache_threshold: float = Field(default=0.95, alias="SEMANTIC_CACHE_THRESHOLD")


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Lấy instance settings (singleton)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """Reload settings (hữu ích cho testing)"""
    global _settings
    _settings = Settings()
    return _settings
