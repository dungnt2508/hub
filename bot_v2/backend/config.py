"""Configuration management for bot_v2

Cấu hình sử dụng Pydantic Settings để tự động đọc từ:
- Environment variables (ưu tiên cao nhất)
- .env file
- Default values (chỉ dùng cho development)

Lưu ý: Tất cả các giá trị default chỉ dùng cho development.
Production PHẢI set các environment variables tương ứng.
"""
from typing import Optional, Any
try:
    from pydantic_settings import BaseSettings
    from pydantic import Field, model_validator, computed_field, ConfigDict
except ImportError:
    from pydantic import BaseSettings, Field, model_validator, computed_field, ConfigDict


class Settings(BaseSettings):
    """Application settings - tự động đọc từ env vars và .env file
    
    Pydantic Settings sẽ tự động:
    1. Đọc từ environment variables (ưu tiên cao nhất)
    2. Đọc từ .env file
    3. Sử dụng default values nếu không có trong env
    
    Ví dụ: DATABASE_URL trong env sẽ override default value
    """
    
    # ==================== Database ====================
    database_url: str = Field(
        default="postgresql+asyncpg://bot_user:bot_pw@localhost:5432/bot_v2_db",
        description="PostgreSQL connection URL. REQUIRED trong production."
    )
    
    db_connection_encryption_key: Optional[str] = Field(
        default=None,
        description="Key để encrypt database connection (optional)"
    )
    
    mcp_db_server_url: Optional[str] = Field(
        default=None,
        description="MCP DB Server URL (optional, ví dụ: http://localhost:8387)"
    )
    
    # ==================== Application Info ====================
    environment: str = Field(
        default="dev",
        description="Environment: dev, staging, production"
    )
    
    debug: bool = Field(
        default=False,
        description="Debug mode (enable/disable)"
    )
    
    app_name: str = Field(
        default="Bot V2",
        description="Application name"
    )
    
    app_version: str = Field(
        default="2.0.0",
        description="Application version"
    )
    
    # ==================== API Server ====================
    api_host: str = Field(
        default="0.0.0.0",
        description="API server host. Có thể set qua HOST hoặc API_HOST env var."
    )
    
    api_port: int = Field(
        default=8386,
        description="API server port. Có thể set qua PORT hoặc API_PORT env var."
    )
    
    api_prefix: str = Field(
        default="/api/v1",
        description="API route prefix"
    )
    
    # ==================== Security ====================
    # JWT_SECRET hoặc SECRET_KEY đều được chấp nhận (JWT_SECRET ưu tiên)
    secret_key: str = Field(
        default="change-me-in-production",
        description="Secret key cho JWT và encryption. REQUIRED trong production. Có thể set qua JWT_SECRET hoặc SECRET_KEY env var."
    )
    
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT algorithm. Có thể set qua JWT_ALGORITHM env var."
    )
    
    # JWT_EXPIRES_IN format: "7d", "24h", "3600s" hoặc số giờ
    jwt_expiration_hours: int = Field(
        default=24,
        description="JWT expiration time in hours. Có thể set qua JWT_EXPIRES_IN (format: 7d, 24h) hoặc JWT_EXPIRATION_HOURS."
    )
    
    jwt_required_iss: Optional[str] = Field(
        default=None,
        description="JWT issuer (iss claim) - required nếu set. Set qua JWT_REQUIRED_ISS env var."
    )
    
    jwt_required_aud: Optional[str] = Field(
        default=None,
        description="JWT audience (aud claim) - required nếu set. Set qua JWT_REQUIRED_AUD env var."
    )
    
    # Catalog Service Integration (optional)
    catalog_service_url: Optional[str] = Field(
        default=None,
        description="Catalog Service URL để validate JWT tokens (optional). Set qua CATALOG_SERVICE_URL env var."
    )
    
    # ==================== LLM Provider (Optional) ====================
    # Chỉ dùng cho intent resolution khi có nhiều candidate intents
    llm_provider: Optional[str] = Field(
        default=None,
        description="LLM provider: 'openai', 'anthropic', etc. (optional)"
    )
    
    llm_api_key: Optional[str] = Field(
        default=None,
        description="LLM API key (required nếu llm_provider được set)"
    )
    
    llm_model: Optional[str] = Field(
        default="gpt-4o-mini",
        description="LLM model name"
    )
    
    llm_base_url: Optional[str] = Field(
        default=None,
        description="LLM API base URL (optional, dùng cho custom endpoints)"
    )
    
    # ==================== Logging ====================
    log_level: str = Field(
        default="INFO",
        description="Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL"
    )
    
    # ==================== CORS ====================
    # CORS origins được lưu dạng string (comma-separated) và parse thành list
    # Sử dụng alias để map CORS_ORIGINS env var vào field này
    cors_origins_str: str = Field(
        default="http://localhost:3000,http://localhost:3001,http://localhost:3002,http://localhost:8387",
        description="CORS allowed origins (comma-separated string). Set CORS_ORIGINS env var để override.",
        alias="CORS_ORIGINS"  # Map env var CORS_ORIGINS vào field này
    )
    
    @model_validator(mode="before")
    @classmethod
    def parse_env_vars(cls, data: Any) -> Any:
        """Map các env vars từ env.example vào các field tương ứng và loại bỏ các field không cần thiết"""
        if isinstance(data, dict):
            # Danh sách các field được phép (tên field trong Settings class)
            allowed_fields = {
                "database_url", "db_connection_encryption_key", "mcp_db_server_url",
                "environment", "debug", "app_name", "app_version",
                "api_host", "api_port", "api_prefix",
                "secret_key", "jwt_algorithm", "jwt_expiration_hours",
                "jwt_required_iss", "jwt_required_aud", "catalog_service_url",
                "llm_provider", "llm_api_key", "llm_model", "llm_base_url",
                "log_level", "cors_origins_str"
            }
            
            # Map CORS_ORIGINS (từ env var) vào cors_origins_str
            if "CORS_ORIGINS" in data:
                data["cors_origins_str"] = data.pop("CORS_ORIGINS")
            elif "cors_origins" in data:
                data["cors_origins_str"] = data.pop("cors_origins")
            
            # Map JWT_SECRET -> secret_key (JWT_SECRET ưu tiên hơn SECRET_KEY)
            if "JWT_SECRET" in data:
                data["secret_key"] = data.pop("JWT_SECRET")
            # SECRET_KEY vẫn được giữ nguyên nếu không có JWT_SECRET
            
            # Map JWT_ALGORITHM -> jwt_algorithm
            if "JWT_ALGORITHM" in data:
                data["jwt_algorithm"] = data.pop("JWT_ALGORITHM")
            
            # Map JWT_EXPIRES_IN -> jwt_expiration_hours
            # Format: "7d", "24h", "3600s" hoặc số giờ
            if "JWT_EXPIRES_IN" in data:
                expires_in = data.pop("JWT_EXPIRES_IN")
                if isinstance(expires_in, str):
                    # Parse format như "7d", "24h", "3600s"
                    if expires_in.endswith("d"):
                        hours = int(expires_in[:-1]) * 24
                    elif expires_in.endswith("h"):
                        hours = int(expires_in[:-1])
                    elif expires_in.endswith("s"):
                        hours = int(expires_in[:-1]) // 3600
                    else:
                        # Assume hours nếu không có suffix
                        hours = int(expires_in)
                    data["jwt_expiration_hours"] = hours
            
            # Map CATALOG_SERVICE_URL -> catalog_service_url
            if "CATALOG_SERVICE_URL" in data:
                data["catalog_service_url"] = data.pop("CATALOG_SERVICE_URL")
            
            # Map HOST -> api_host, PORT -> api_port (nếu chưa có API_HOST, API_PORT)
            if "HOST" in data and "api_host" not in data:
                data["api_host"] = data.pop("HOST")
            if "PORT" in data and "api_port" not in data:
                try:
                    data["api_port"] = int(data.pop("PORT"))
                except (ValueError, TypeError):
                    pass  # Giữ nguyên default nếu không parse được
            
            # Map ENVIRONMENT -> environment
            if "ENVIRONMENT" in data:
                data["environment"] = data.pop("ENVIRONMENT")
            
            # Map DEBUG -> debug (convert string "true"/"false" to bool)
            if "DEBUG" in data:
                debug_val = data.pop("DEBUG")
                if isinstance(debug_val, str):
                    data["debug"] = debug_val.lower() in ("true", "1", "yes", "on")
                else:
                    data["debug"] = bool(debug_val)
            
            # Map APP_NAME -> app_name
            if "APP_NAME" in data:
                data["app_name"] = data.pop("APP_NAME")
            
            # Map APP_VERSION -> app_version
            if "APP_VERSION" in data:
                data["app_version"] = data.pop("APP_VERSION")
            
            # Loại bỏ tất cả các field không được phép (không có trong allowed_fields)
            # Giữ lại các field đã được map và các field có trong allowed_fields
            keys_to_remove = [key for key in data.keys() if key.lower() not in allowed_fields]
            for key in keys_to_remove:
                data.pop(key, None)
        
        return data
    
    @computed_field
    @property
    def cors_origins(self) -> list[str]:
        """Parse CORS origins từ comma-separated string thành list
        
        Sử dụng như: settings.cors_origins (không phải cors_origins_str)
        """
        return [origin.strip() for origin in self.cors_origins_str.split(",") if origin.strip()]

    
    # Pydantic v2 configuration
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore các env vars không được định nghĩa trong class
        # Cho phép đọc env vars với cả uppercase và lowercase
        # Ví dụ: DATABASE_URL và database_url đều được chấp nhận
    )


# Tạo settings instance - sẽ tự động đọc từ env vars và .env file
settings = Settings()
