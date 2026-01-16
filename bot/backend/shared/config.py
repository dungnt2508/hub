"""
Runtime Configuration
"""
import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
# Look for .env in current directory, then project root
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
    print(f"[OK] Loaded .env from: {env_path}")
else:
    print(f"[WARNING] .env file not found at: {env_path}")
    # Try loading from current working directory as fallback
    load_dotenv()


class RouterConfig:
    """Router configuration from environment variables"""
    
    def __init__(self):
        # ==================== APP ====================
        self.APP_NAME = os.getenv("APP_NAME", "Hub Bot Router")
        self.APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")
        self.DEBUG = os.getenv("DEBUG", "false").lower() == "true"
        self.HOST = os.getenv("HOST", "0.0.0.0")
        self.PORT = int(os.getenv("PORT", "8386"))
        self.RELOAD = os.getenv("RELOAD", "false").lower() == "true"
        
        # ==================== DATABASE ====================
        self.DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://bot_user:bot_pw@127.0.0.1:5432/bot_db")
        
        # ==================== REDIS ====================
        self.REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.REDIS_MAX_CONNECTIONS = int(os.getenv("REDIS_MAX_CONNECTIONS", "50"))
        
        # ==================== SESSION ====================
        self.SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "2592000"))  # 30 days
        self.SESSION_CACHE_TTL = int(os.getenv("SESSION_CACHE_TTL", "300"))
        self.CONVERSATION_TIMEOUT_MINUTES = int(os.getenv("CONVERSATION_TIMEOUT_MINUTES", "10"))  # 10 minutes (F4.2)
        self.ESCALATION_RETRY_THRESHOLD = int(os.getenv("ESCALATION_RETRY_THRESHOLD", "3"))  # Escalate after 3 retries (F4.3)
        
        # ==================== ROUTER ====================
        self.MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", "5000"))
        self.ENABLE_PATTERN = os.getenv("ENABLE_PATTERN", "true").lower() == "true"
        self.ENABLE_KEYWORD = os.getenv("ENABLE_KEYWORD", "true").lower() == "true"
        self.ENABLE_EMBEDDING = os.getenv("ENABLE_EMBEDDING", "true").lower() == "true"
        self.ENABLE_LLM_FALLBACK = os.getenv("ENABLE_LLM_FALLBACK", "true").lower() == "true"
        self.EMBEDDING_THRESHOLD = float(os.getenv("EMBEDDING_THRESHOLD", "0.8"))
        self.LLM_THRESHOLD = float(os.getenv("LLM_THRESHOLD", "0.65"))
        
        # ==================== STEP TIMEOUTS (ms) ====================
        self.STEP_SESSION_TIMEOUT = int(os.getenv("STEP_SESSION_TIMEOUT", "50"))
        self.STEP_META_TIMEOUT = int(os.getenv("STEP_META_TIMEOUT", "20"))
        self.STEP_PATTERN_TIMEOUT = int(os.getenv("STEP_PATTERN_TIMEOUT", "30"))
        self.STEP_KEYWORD_TIMEOUT = int(os.getenv("STEP_KEYWORD_TIMEOUT", "20"))
        self.STEP_EMBEDDING_TIMEOUT = int(os.getenv("STEP_EMBEDDING_TIMEOUT", "10000"))
        self.STEP_LLM_TIMEOUT = int(os.getenv("STEP_LLM_TIMEOUT", "15000"))  # 15 seconds for LLM classification
        
        # ==================== AI ROUTING ====================
        self.AI_PROVIDER_PRIMARY = os.getenv("AI_PROVIDER_PRIMARY", "litellm")
        self.AI_PROVIDER_FALLBACK = os.getenv("AI_PROVIDER_FALLBACK", "openai")
        
        # ==================== LLM ROUTER ====================
        self.LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "30"))
        self.LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
        
        # ==================== LITELLM ====================
        self.LITELLM_API_BASE = os.getenv("LITELLM_API_BASE", "http://127.0.0.1:4000")
        self.LITELLM_API_KEY = os.getenv("LITELLM_API_KEY", "litellm-proxy-key")
        self.LITELLM_CHAT_MODEL = os.getenv("LITELLM_CHAT_MODEL", "gpt-4o-mini")
        self.LITELLM_EMBEDDING_MODEL = os.getenv("LITELLM_EMBEDDING_MODEL", "text-embedding-3-large")
        
        # ==================== OPENAI (FALLBACK) ====================
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        self.OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
        self.OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")
        self.OPENAI_TIMEOUT = int(os.getenv("OPENAI_TIMEOUT", "30"))
        
        # # Debug: Log loaded config
        # print(f"\n[INFO] AI Provider Config Loaded:")
        # print(f"  LITELLM_API_BASE: {self.LITELLM_API_BASE}")
        # print(f"  LITELLM_API_KEY: {'SET' if self.LITELLM_API_KEY and self.LITELLM_API_KEY != 'litellm-proxy-key' else 'DEFAULT'}")
        # print(f"  OPENAI_API_KEY: {'SET' if self.OPENAI_API_KEY else 'NOT SET'}\n")
        
        # ==================== EMBEDDING ====================
        self.EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai")
        self.EMBEDDING_CACHE_TTL = int(os.getenv("EMBEDDING_CACHE_TTL", "86400"))
        
        # ==================== LOGGING ====================
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_FORMAT = os.getenv("LOG_FORMAT", "json")
        
        # ==================== TRACING (OpenTelemetry) ====================
        self.ENABLE_TRACING = os.getenv("ENABLE_TRACING", "true").lower() == "true"
        self.JAEGER_ENDPOINT = os.getenv("JAEGER_ENDPOINT", None)  # e.g., http://localhost:4317
        self.OTEL_CONSOLE_EXPORT = os.getenv("OTEL_CONSOLE_EXPORT", "true").lower() == "true"
        
        # ==================== FEATURE FLAGS ====================
        self.FEATURE_EMBEDDING_CLASSIFIER = os.getenv("FEATURE_EMBEDDING_CLASSIFIER", "true").lower() == "true"
        self.FEATURE_LLM_CLASSIFIER = os.getenv("FEATURE_LLM_CLASSIFIER", "true").lower() == "true"
        
        # ==================== RETRY & CIRCUIT BREAKER ====================
        self.MAX_RETRY_COUNT = int(os.getenv("MAX_RETRY_COUNT", "3"))
        self.MAX_SLOTS_PER_REQUEST = int(os.getenv("MAX_SLOTS_PER_REQUEST", "20"))
        self.CIRCUIT_BREAKER_FAILURE_THRESHOLD = int(os.getenv("CIRCUIT_BREAKER_FAILURE_THRESHOLD", "5"))
        self.CIRCUIT_BREAKER_TIMEOUT = int(os.getenv("CIRCUIT_BREAKER_TIMEOUT", "60"))  # seconds
        
        # ==================== VECTOR STORE (QDRANT) ====================
        self.QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)
        self.VECTOR_DIMENSION = int(os.getenv("VECTOR_DIMENSION", "1536"))  # OpenAI embedding dimension
        
        # ==================== CATALOG SERVICE ====================
        self.CATALOG_API_URL = os.getenv("CATALOG_API_URL", "http://localhost:8385")
        
        self._validate()
    
    def _validate(self):
        """Validate configuration"""
        if not 0.0 <= self.EMBEDDING_THRESHOLD <= 1.0:
            raise ValueError("EMBEDDING_THRESHOLD must be between 0 and 1")
        if not 0.0 <= self.LLM_THRESHOLD <= 1.0:
            raise ValueError("LLM_THRESHOLD must be between 0 and 1")
        if not 0.0 <= self.LLM_TEMPERATURE <= 2.0:
            raise ValueError("LLM_TEMPERATURE must be between 0 and 2")
        if self.MAX_MESSAGE_LENGTH <= 0:
            raise ValueError("MAX_MESSAGE_LENGTH must be positive")
        if self.SESSION_TTL_SECONDS <= 0:
            raise ValueError("SESSION_TTL_SECONDS must be positive")
        if self.LLM_TIMEOUT <= 0:
            raise ValueError("LLM_TIMEOUT must be positive")
        if self.MAX_RETRY_COUNT < 0:
            raise ValueError("MAX_RETRY_COUNT must be >= 0")
        if self.MAX_SLOTS_PER_REQUEST <= 0:
            raise ValueError("MAX_SLOTS_PER_REQUEST must be positive")
        if self.CIRCUIT_BREAKER_FAILURE_THRESHOLD <= 0:
            raise ValueError("CIRCUIT_BREAKER_FAILURE_THRESHOLD must be positive")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary (non-sensitive)"""
        return {
            "APP_NAME": self.APP_NAME,
            "APP_VERSION": self.APP_VERSION,
            "ENVIRONMENT": self.ENVIRONMENT,
            "EMBEDDING_THRESHOLD": self.EMBEDDING_THRESHOLD,
            "LLM_THRESHOLD": self.LLM_THRESHOLD,
            "MAX_MESSAGE_LENGTH": self.MAX_MESSAGE_LENGTH,
            "SESSION_TTL_SECONDS": self.SESSION_TTL_SECONDS,
            "LLM_TIMEOUT": self.LLM_TIMEOUT,
            "ENABLE_LLM_FALLBACK": self.ENABLE_LLM_FALLBACK,
            "MAX_RETRY_COUNT": self.MAX_RETRY_COUNT,
            "MAX_SLOTS_PER_REQUEST": self.MAX_SLOTS_PER_REQUEST,
        }


# Global config instance
config = RouterConfig()

