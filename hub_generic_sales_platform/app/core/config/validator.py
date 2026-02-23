"""
Config Validator Module

Validates application configuration at startup to prevent runtime errors.
"""
from typing import List, Optional
import re
from app.core.config.settings import Settings
from app.core.shared.logger import get_logger

logger = get_logger(__name__, component="config_validator")


class ConfigValidationError(ValueError):
    """Raised when configuration is invalid"""
    pass


class ConfigValidator:
    """
    Validates application configuration at startup
    """
    
    WEAK_SECRETS = [
        "sumy23122",
        "your-secret-key",
        "change-me",
        "secret",
        "password",
        "12345",
        "test",
        "demo"
    ]
    
    MIN_SECRET_KEY_LENGTH = 32
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_all(self, strict: bool = True) -> None:
        """Run all validations"""
        logger.info("Starting configuration validation...")
        
        self.validate_database_config()
        self.validate_ai_provider_config()
        self.validate_environment_setting()
        
        if self.errors:
            error_msg = f"Configuration validation failed with {len(self.errors)} error(s):\n" + \
                       "\n".join(f"  - {err}" for err in self.errors)
            logger.error(error_msg)
            if strict:
                raise ConfigValidationError(error_msg)
        
        if self.warnings:
            warning_msg = f"Configuration has {len(self.warnings)} warning(s):\n" + \
                         "\n".join(f"  - {warn}" for warn in self.warnings)
            logger.warning(warning_msg)
        
        if not self.errors and not self.warnings:
            logger.info("Configuration validation passed")
    
    def validate_database_config(self) -> None:
        """Validate database configuration"""
        db_url = self.settings.database_url
        
        if not db_url:
            self.errors.append("DATABASE_URL is required but not set")
            return
        
        if not db_url.startswith(("postgresql://", "postgresql+asyncpg://", "sqlite://", "sqlite+aiosqlite://")):
            self.errors.append(
                f"DATABASE_URL has invalid format. Expected postgresql:// or sqlite://, got: {db_url[:20]}..."
            )
    
    def validate_ai_provider_config(self) -> None:
        """Validate AI provider configuration"""
        primary_provider = self.settings.ai_provider_primary
        
        if not primary_provider:
            self.warnings.append("PRIMARY_AI_PROVIDER not set")
            return
        
        if primary_provider == "litellm":
            if not self.settings.litellm_api_key:
                self.warnings.append("LITELLM_API_KEY is not set while provider is 'litellm'")
        elif primary_provider == "openai":
            if not self.settings.openai_api_key:
                self.warnings.append("OPENAI_API_KEY is not set while provider is 'openai'")
    
    def validate_environment_setting(self) -> None:
        """Validate environment setting"""
        env = self.settings.environment
        valid_environments = ["dev", "development", "test", "staging", "prod", "production"]
        if env not in valid_environments:
            self.warnings.append(f"ENVIRONMENT='{env}' is not a standard value.")
    
    def get_error_summary(self) -> str:
        """Get summary of all errors and warnings"""
        lines = []
        if self.errors:
            lines.append(f"Errors:")
            for err in self.errors:
                lines.append(f"  - {err}")
        if self.warnings:
            lines.append(f"Warnings:")
            for warn in self.warnings:
                lines.append(f"  - {warn}")
        return "\n".join(lines) if lines else "No errors or warnings"


def validate_config_on_startup(settings: Settings, strict: bool = True) -> None:
    """Convenience function to validate config on app startup"""
    validator = ConfigValidator(settings)
    validator.validate_all(strict=strict)
