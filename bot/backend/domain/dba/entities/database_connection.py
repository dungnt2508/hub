"""
Database Connection Entity
"""
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
from cryptography.fernet import Fernet
import os
import base64


class DatabaseType(str, Enum):
    """Database types"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLSERVER = "sqlserver"
    MONGODB = "mongodb"
    ORACLE = "oracle"
    SQLITE = "sqlite"


class ConnectionStatus(str, Enum):
    """Connection status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    TESTING = "testing"


class DatabaseConnection(BaseModel):
    """Database connection entity"""
    
    connection_id: Optional[str] = Field(None, description="Connection ID (UUID)")
    name: str = Field(..., description="Connection name (e.g., 'SQL Server Production')")
    db_type: DatabaseType = Field(..., description="Database type")
    connection_string: str = Field(..., description="Encrypted connection string")
    
    # Metadata
    description: Optional[str] = Field(None, description="Connection description")
    environment: Optional[str] = Field(None, description="Environment (prod, staging, dev)")
    tags: Optional[list[str]] = Field(None, description="Tags for grouping")
    
    # Status
    status: ConnectionStatus = Field(ConnectionStatus.ACTIVE, description="Connection status")
    last_tested_at: Optional[datetime] = Field(None, description="Last test timestamp")
    last_error: Optional[str] = Field(None, description="Last error message")
    
    # Access control
    created_by: Optional[str] = Field(None, description="Created by user")
    tenant_id: Optional[str] = Field(None, description="Tenant ID (for multi-tenant)")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @classmethod
    def _get_encryption_key(cls) -> bytes:
        """Get encryption key from environment"""
        key = os.getenv("DB_CONNECTION_ENCRYPTION_KEY")
        if not key:
            # Generate key if not exists (for development only)
            key = Fernet.generate_key().decode()
            print(f"[WARNING] Generated encryption key. Set DB_CONNECTION_ENCRYPTION_KEY={key}")
        return key.encode() if isinstance(key, str) else key
    
    @classmethod
    def encrypt_connection_string(cls, connection_string: str) -> str:
        """Encrypt connection string"""
        key = cls._get_encryption_key()
        fernet = Fernet(key)
        encrypted = fernet.encrypt(connection_string.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    
    @classmethod
    def decrypt_connection_string(cls, encrypted_string: str) -> str:
        """Decrypt connection string"""
        key = cls._get_encryption_key()
        fernet = Fernet(key)
        encrypted = base64.urlsafe_b64decode(encrypted_string.encode())
        decrypted = fernet.decrypt(encrypted)
        return decrypted.decode()
    
    def get_decrypted_connection_string(self) -> str:
        """Get decrypted connection string"""
        return self.decrypt_connection_string(self.connection_string)
    
    def to_dict(self, include_connection_string: bool = False) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = self.dict(exclude_none=True)
        if not include_connection_string:
            # Don't expose encrypted connection string by default
            data.pop("connection_string", None)
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], encrypted: bool = True) -> "DatabaseConnection":
        """Create DatabaseConnection from dictionary"""
        # If connection_string is not encrypted, encrypt it
        if "connection_string" in data and not encrypted:
            data["connection_string"] = cls.encrypt_connection_string(data["connection_string"])
        return cls(**data)

